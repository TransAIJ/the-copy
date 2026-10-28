# コピー盤の動かし方

コピー盤は HTML 1枚（`assets/board/index.html`）です。同じフォルダの `job.json` を1秒ごとに読み、段（stage）に合わせて動きます。`job.json` が無い時は、見本の中身で 1〜7 段を繰り返します。

## job.json の形

```json
{
  "stage": 3,
  "kind": "t2t",
  "use": "X投稿",
  "source": { "title": "元の物の名前", "thumb": "" },
  "parts": [
    { "lane": "t2t", "name": "冒頭の1文", "fixed": "失敗の場面から入る", "blank": "自分の体験", "filled": "" }
  ],
  "output": { "title": "", "thumb": "" },
  "meter": { "over": 0, "under": 0 },
  "share_url": ""
}
```

| 欄 | 中身 |
|---|---|
| stage | 0 待つ・1 見る・2 分ける・3 ①と②・4 埋める・5 型にする・6 作る・7 比べる |
| kind | 主な変換（t2t・i2i・v2v） |
| use | 用途の名前（X投稿・LP など。`uses.md` の言葉） |
| source | 元の物の名前と、小さな画像（コピー盤のフォルダからの相対パス。無ければ空） |
| parts | 部品。lane は変換、fixed は①写す物（構造か見せ方を短く。寸法は書かない）、blank は②の欄の名前、filled は埋めた中身（短く） |
| output | できた物の名前と小さな画像 |
| meter | 写しすぎ（over）と写せていない（under）。0〜100。`judge.md` の数え方 |
| share_url | 最後の画面のボタンで開く URL。無ければボタンを出しません |

コピー盤に出す文字は、名前と中身と今の段だけです。説明の文や宣伝の文を入れません。元の物の本文や他人の画像をそのまま載せず、名前と小さな画像だけにします（他人の画像は、使う人の手元で見るだけの時に限ります）。

## 作業フォルダ（Claude Code・デスクトップアプリの Code タブ）

```bash
# 最初の1回（Step 0）: 盤を置いて開く（小さなサーバーを裏で立てる。job.json が15分変わらないと自分で止まる）
python3 scripts/board.py --dir .the-copy/board --init --serve 8765
# Step 1〜7 のそれぞれを始める時に1回ずつ（段を飛ばさない）
python3 scripts/board.py --dir .the-copy/board --stage 2 --job job-draft.json
```

- `--serve` は `http://localhost:8765/` で盤を開けるようにします。Code タブではブラウザの枠で、端末ではいつものブラウザで開きます
- `job.json` と同じ中身の `job.js` も書くので、サーバー無しで `index.html` を直接開いても動きます
- `--job` に渡す JSON は、変わった欄だけでかまいません（前の中身に重ねます）
- Python が無い時は、Claude が `.the-copy/board/job.json` と `job.js`（`window.THE_COPY_JOB = {…};`）を直接書き、`index.html` を開いてもらいます
- 段は Step 1〜7 を始めるたびに1つずつ書きます。まとめて最後に 7 を書くと、盤が途中を飛ばし、使う人には何をしているかが見えません
- 最後の段（7）を書いた後も、裏のサーバーは止めません。盤は job.json を読んで最後の段の動きを出すのに数秒かかり、止めると盤が前の段のまま止まります。サーバーは job.json が15分変わらないと自分で止まります（`--idle-exit` で分を変えられます）

## チャット（claude.ai のウェブ・デスクトップのチャット）

段ごとに出し直すと、使う人の枠を使いすぎます。**Step 2 の後と Step 7 の後の2回だけ**出します。

```bash
python3 scripts/board.py --inline --job job.json --play --out /mnt/user-data/outputs/copy-board.html
```

- `--inline` は、盤と job を1枚の HTML にまとめます。`--play` を付けると、1段から今の段まで順に動いてから止まります
- できた HTML を、HTML の Artifact として出すか、ファイルとして渡します。ファイルを直接開けない画面では、中身をそのまま Artifact にします
- コードを動かせない設定の時は、盤を出さずに、今の段と部品の表を文字で出します（「設定 > 機能」で「コードの実行とファイルの作成」をオンにすると盤が出ます、と1行添えます）
