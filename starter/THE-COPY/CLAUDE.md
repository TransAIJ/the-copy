# THE・COPY の作業フォルダ

このフォルダでは THE・COPY を使います。他人のコンテンツが売れている理由・構造・中身・情報量を真似して、自分の素材で同じ質のものを作る時は、
`.claude/skills/the-copy/SKILL.md` の手順に従ってください。

- 使う人の素材（②）は `素材/` にあります。作る前に `素材/わたし.md` を読みます
- 真似したい他人のものは `素材/お手本/` に置かれます
- 作ったものは `完成/<日付>-<名前>/` に置きます
- 作る前に、先に `python3 .claude/skills/the-copy/scripts/rename_folders.py` を1回動かします（0.2 で作ったフォルダを新しい名前に移す台本。わたし.md と型は消えません。移すものが無ければ何もしません）
- できた型（スキル）は `.claude/skills/<ブランド>-<用途>-<型>/` に置きます。次から同じ種類のものはその型で作ります
- 台本は各スキルのフォルダの `scripts/` にあります（例: `python3 .claude/skills/the-copy/scripts/board.py`）。Python が無い時は、Claude が読んで数えます
- お手本と同じ言い回しを数える時は、作業フォルダから `python3 .claude/skills/copy-text/scripts/text_stats.py --compare <お手本> <作ったもの>` を動かします。台本は作業フォルダから、この形の道筋で動かします（`cd` でスキルのフォルダに入ってから動かしません）
- ダッシュボードは `.the-copy/board/` に置き、`mkdir -p .the-copy/board && nohup python3 .claude/skills/the-copy/scripts/board.py --dir .the-copy/board --init --serve 8765 > .the-copy/serve.log 2>&1 &` で裏に回して開きます（「裏の作業が終わった」と出ても、サーバーは動き続けています）。Step 1〜7 を始めるたびに `--stage <ステップ>` で1回ずつ書き、最後に 7 を書いた後もサーバーは止めません
- 使う人の API キーやトークンを読み上げない・書き出さない。外に何も送らない
