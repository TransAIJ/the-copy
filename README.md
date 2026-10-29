# THE・COPY

伸びている他人のコンテンツを部品に分けて、売れている理由・構造・中身・情報量を写し、実績や写真は自分の素材で埋めて、同じ質の物を何度でも作れる型（スキル）を残す道具です。あなたが契約している Claude の中で動きます。

- 文章は **t2t**（text to text）、画像と画面の配置は **i2i**（image to image）、動画は **v2v**（video to video）で作ります
- SNS投稿・SEO記事・インスタ画像・ショート動画・YouTube・LP・スライド・VSL・アプリの画面に使えます
- コピーしている間は、コピー盤（HTML 1枚）に「見る → 分ける → ①と② → 埋める → 型にする → 作る → 比べる」が動きで出ます
- AI の代金は、あなたの Claude の契約（定額）の中です。THE・COPY が別にお金を取ったり、外にデータを送ったりはしません

## 始め方（入口は3つ）

| 入口 | 向いている人 | 時間の目安 |
|---|---|---|
| ① ブラウザだけ（claude.ai） | まず試したい人。文章（X投稿など）を作れます | 3〜5分 |
| ② パソコンの作業フォルダ（Claude デスクトップアプリの Code タブ） | コピー盤の動きと、画像・動画まで使いたい人 | 10〜15分 |
| ③ 端末（Claude Code） | エンジニア | 1分 |

時間は目安で、Claude に入っている前提です。動かすには、Claude の有料プラン（Pro 以上）が必要です。

### ① ブラウザだけ（claude.ai）

ブラウザで作れるのは、文章（X投稿など）です。コピー盤の動きと、画像・動画は、②のパソコンの入口で使います。

1. 設定 > 機能（Settings > Capabilities）で「コードの実行とファイルの作成」（英語の画面では Create and edit files）をオンにします
2. カスタマイズ > プラグイン（Customize > Plugins）> 追加 > マーケットプレイスを追加 に `TransAIJ/the-copy` を入れ、THE・COPY を追加します。zip を受け取った人は「プラグインをアップロード」から `the-copy.zip` を選びます
3. 入力欄で `/` を押して THE・COPY を選び、手本にしたい物（本文・スクショ・URL）と、作りたい物を渡します

### ② パソコンの作業フォルダ（Code タブ）

1. Claude デスクトップアプリを入れてログインします
2. `the-copy-starter.zip`（このリポジトリの `starter/` と同じ物）を落として展開します
3. Code タブで「フォルダを開く」から、展開した `THE-COPY` フォルダを開き、信頼の確認で「はい」を選びます
4. `素材棚/わたし.md` を埋めます（埋めずに始めても、THE・COPY が1回だけ質問します）
5. 「THE・COPY で、素材棚/元の物/ の投稿の作り方で X 投稿を1本作って」のように頼みます

動画を扱う時は ffmpeg が、LP の区画を台本で拾う時は Node.js と Playwright が要ります。無ければ Claude に「入れて」と頼めば入れてくれます。

### ③ 端末（Claude Code）

```bash
claude plugin install the-copy --marketplace TransAIJ/the-copy
```

または Claude Code の中で `/plugin marketplace add TransAIJ/the-copy` → `/plugin install the-copy@the-copy`。

## スキル版（いちばん早く試す）

THE・COPY を1つのスキルにまとめた `the-copy-skill.zip` です。手本の X 投稿が1つ入っているので、受け取ってすぐ1本作れます。

- 落とす: https://github.com/TransAIJ/the-copy/releases/latest/download/the-copy-skill.zip
- Claude Code: zip を展開し、`the-copy` フォルダを作業フォルダの `.claude/skills/`（どのフォルダでも使うなら `~/.claude/skills/`）に置きます。`claude` を起動して `/` を押すと `the-copy` が出ます
- claude.ai: 設定 > 機能（Settings > Capabilities）のスキルで、zip をそのままアップロードします
- 最初の1本の頼み方: `THE・COPYで、同梱の手本の作り方で、私の商品のX投稿を1本作って`。商品・誰に売るか・実績の3つを聞かれるので、答えると X 投稿が1本できます
- プラグイン版と一緒に入れても、名前はぶつかりません（スキル版は `/the-copy`、プラグイン版は `/the-copy:the-copy`）

同梱の手本（`examples/x-moto.txt`）は、作者の会社が自分で出した X 投稿です。手本の文と例は写さず、作り方だけを写します。

## 中身

| スキル | 呼び方 | すること |
|---|---|---|
| the-copy | `/the-copy:the-copy` | 入口。0〜7段の流れ、素材棚、型の書き方、写しすぎの判定、コピー盤 |
| copy-text | `/the-copy:copy-text` | 文章（t2t）。1文ずつ読んで売れている理由・話の順番・論点・情報量を写し、元と同じ言い回しを数えて落とす |
| copy-image | `/the-copy:copy-image` | 画像と画面（i2i）。区画の順と役割・見せ方・情報の数を写して HTML で作る。写真の層は使う人の画像のモデル |
| copy-video | `/the-copy:copy-video` | 動画（v2v）。元の動画が話したことを箇条書きにして、台本・カット表・テロップ表を作る。縦の動画の書き出しも |

台本（Python と Node.js）は、無くても Claude が読んで数える形を既定にしています。台本は外に通信しません（`image_api.py` と `api/` を、あなたが鍵を入れて動かした時を除きます）。

## 写してよい物・写さない物

- 写すのは、売れている理由、構造（話の順番・区画の順・見せ方）、中身（扱っている話題と論点）、情報量（項目・事例・手順の数）です
- 写さないのは、寸法（文字の px・余白・字の大きさ・1文の字数）と言い回しです。寸法は自分のブランドの決まりと読みやすさで決めます
- 実績・数字・体験・写真・声・商品は、自分の物で埋めます。元の画像・ロゴ・イラスト・お客様の声・人の顔は使いません
- 作った後に、元と並べて「写しすぎ」と「写せていない」を判定し、写しすぎなら出しません
- 他人の YouTube の動画はダウンロードしません。ログインの要るページを裏から取りに行きません
- 作風や構成や扱う話題はアイデアで、写してよい範囲です。ただし画像を入力して作る i2i は元に依拠したと見られやすく、表現が似れば著作権の侵害になり得ます（文化庁「AIと著作権に関する考え方について」2024年3月）。出す前の判断は、使う人の責任です

## API で動かす（任意・既定では使いません）

定額の Claude で足りる人は、この節は要りません。自分で API キーを用意して、従量で動かしたい人のための口です。どれも、あなたが鍵を入れた時だけ動き、鍵を画面やファイルに出しません。

| 口 | 使い方 | 向いていること |
|---|---|---|
| 1. Claude Code に API キー | 端末で `ANTHROPIC_API_KEY` を入れて Claude Code を動かすと、このプラグインが従量で動きます | 定額の枠を超えて大量に回す時 |
| 2. Claude API の Skills | `pip install -r api/requirements.txt` → `python3 api/upload_skills.py` でスキル4本を上げ、`python3 api/run_api.py --source 元.txt --ask "..."` で動かします | 文章と HTML の部品を、ほかの仕組みから自動で作る時（API の箱はネットと ffmpeg が使えないので、動画と写真は不可） |
| 3. 画像の API キー | `.env` に `OPENAI_API_KEY` か `GEMINI_API_KEY` を入れ、`skills/copy-image/scripts/image_api.py` で写真の層を作ります | 写真の i2i を自動で作る時（既定は、ChatGPT か Gemini のアプリに手で貼る方法） |

料金は各社の料金表のとおりで、あなたの契約に請求されます。

## 鍵と通信

- THE・COPY はあなたの Claude のログインに触れません。ログインは Anthropic の画面で、あなたが行います
- API キーは、あなたが自分で入れた時だけ、環境変数か `.env` から読みます。`.env` は git に入らないようにしてあります
- コピー盤は外に通信しません（`share_url` を入れた時の最後のボタンだけが、そのページを開きます）

## ライセンス

MIT License。改変・再配布・商用利用ができます。詳しくは `LICENSE` を見てください。

「Claude」は Anthropic の商標です。THE・COPY は Anthropic が作った物でも、Anthropic と組んでいる物でもありません。
