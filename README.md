# pachi-live-playlists

VRChat ワールド「Pachi ya」の YamaPlayer（ダイナミックプレイリスト）用に、
YouTube チャンネルごとの「いま配信中のライブ一覧」を 15 分ごとに自動更新して配信するリポジトリです。

## しくみ

1. GitHub Actions が 15 分ごとに `scripts/update_playlists.py` を実行
2. yt-dlp で各チャンネルの「ライブ」タブを読み、配信中のものだけを視聴者数の多い順に並べる
3. YamaPlayer が読める形式の JSON を `docs/<id>.json` に書き出してコミット
4. GitHub Pages が `https://<ユーザー名>.github.io/pachi-live-playlists/<id>.json` で配信
5. ワールド側の `YamaDynamicPlaylistAutoPlay` がその URL をダイナミックプレイリストとして追加

| id | チャンネル | ワールドで使う URL |
|---|---|---|
| ntv | 日テレNEWS | `https://<ユーザー名>.github.io/pachi-live-playlists/ntv.json` |
| tbs | TBS NEWS DIG Powered by JNN | `https://<ユーザー名>.github.io/pachi-live-playlists/tbs.json` |
| weathernews | ウェザーニュース | `https://<ユーザー名>.github.io/pachi-live-playlists/weathernews.json` |

## セットアップ

1. このフォルダの中身で **公開（Public）** リポジトリ `pachi-live-playlists` を作って push
2. Settings → Pages → Source を「Deploy from a branch」、Branch を `main` / `/docs` にして Save
3. Actions タブ → 「Update live playlists」→「Run workflow」で一度手動実行
4. 数分後に上の URL をブラウザで開き、JSON が表示されれば完了

## チャンネルを増やす・変える

`scripts/channels.json` に `{ "id": "...", "title": "...", "url": "https://www.youtube.com/@ハンドル/streams" }` を追加して push。
ワールド側の `Playlist Urls` にも同じ id の URL を追加します。

## 注意

- 公開リポジトリの定期実行は、60 日間リポジトリに更新が無いと GitHub が自動停止します。
  このワークフロー自身がコミットするので、配信に変化があれば止まりません。止まったときは Actions 画面で再開できます。
- YouTube 側の仕様変更や、GitHub のサーバーからのアクセス制限で一覧が取れないことがあります。
  そのときは前回のファイルを残すので、ワールド側には古い一覧が出続けます（Actions の実行ログで確認できます）。
