"""
チャンネルごとに「いま配信中のライブ」を調べ、YamaPlayer のダイナミックプレイリストが
読み込める形式の JSON を docs/<id>.json に書き出す。

YamaPlayer は読み込んだ文字列の中から {"playlist": ...} を探し、
playlist.title をプレイリスト名、playlist.contents[].playlistPanelVideoRenderer の
videoId / title.simpleText を曲として並べる（YouTube.GetPlaylistFromHtml）。
その形をそのまま作って GitHub Pages で配信する。

使い方:  python scripts/update_playlists.py
必要:    pip install yt-dlp
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANNELS = ROOT / "scripts" / "channels.json"
OUT_DIR = ROOT / "docs"

# ライブ判定の情報が一覧に無いとき、個別に確認する件数の上限
PROBE_LIMIT = 15


def run_ytdlp(args):
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--ignore-errors", *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 and not r.stdout.strip():
        print(r.stderr.strip()[-800:], file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def is_live_entry(e):
    status = e.get("live_status")
    if status is not None:
        return status == "is_live"
    if e.get("is_live") is not None:
        return bool(e.get("is_live"))
    return None  # 不明


def probe_live(video_id):
    info = run_ytdlp(["-J", "--skip-download", f"https://www.youtube.com/watch?v={video_id}"])
    if not info:
        return False, None
    return info.get("live_status") == "is_live", info.get("concurrent_view_count")


def collect_lives(channel_url):
    data = run_ytdlp(["-J", "--flat-playlist", "--playlist-end", "40", channel_url])
    if not data:
        return None  # 取得失敗（前回のファイルを残す）
    entries = [e for e in (data.get("entries") or []) if e and e.get("id")]

    lives, unknown = [], []
    for e in entries:
        live = is_live_entry(e)
        if live is True:
            lives.append({"id": e["id"], "title": e.get("title") or e["id"],
                          "viewers": e.get("concurrent_view_count") or 0})
        elif live is None:
            unknown.append(e)

    # 一覧にライブ判定が無い場合だけ、上から順に個別確認する
    if not lives and unknown:
        for e in unknown[:PROBE_LIMIT]:
            ok, viewers = probe_live(e["id"])
            if ok:
                lives.append({"id": e["id"], "title": e.get("title") or e["id"],
                              "viewers": viewers or 0})

    # 視聴者数の多い順（メインの配信が先頭に来やすい）
    lives.sort(key=lambda x: x["viewers"], reverse=True)
    return lives


def to_yamaplayer_json(title, lives):
    contents = [{
        "playlistPanelVideoRenderer": {
            "videoId": v["id"],
            "title": {"simpleText": v["title"]},
            "badges": [{"metadataBadgeRenderer": {"icon": {"iconType": "LIVE"}}}],
        }
    } for v in lives]
    return {"playlist": {"title": title, "contents": contents}}


def main():
    OUT_DIR.mkdir(exist_ok=True)
    channels = json.loads(CHANNELS.read_text(encoding="utf-8"))
    failed = 0
    for ch in channels:
        lives = collect_lives(ch["url"])
        out = OUT_DIR / f"{ch['id']}.json"
        if lives is None:
            failed += 1
            print(f"[{ch['id']}] 取得に失敗。前回のファイルを残します", file=sys.stderr)
            continue
        out.write_text(json.dumps(to_yamaplayer_json(ch["title"], lives), ensure_ascii=False),
                       encoding="utf-8")
        print(f"[{ch['id']}] 配信中 {len(lives)} 本: " + " / ".join(v["title"] for v in lives))
    # 全チャンネル失敗したときだけエラー終了（Actions の失敗通知に出す）
    return 1 if failed == len(channels) else 0


if __name__ == "__main__":
    sys.exit(main())
