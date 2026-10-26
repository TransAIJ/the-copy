# THE・COPY の作業フォルダ

このフォルダでは THE・COPY を使います。他人のコンテンツが売れている理由・構造・中身・情報量を写して、自分の素材で同じ質の物を作る時は、
`.claude/skills/the-copy/SKILL.md` の手順に従ってください。

- 使う人の素材（②）は `素材棚/` にあります。作る前に `素材棚/わたし.md` を読みます
- 写したい他人の物は `素材棚/元の物/` に置かれます
- 作った物は `できた物/<日付>-<名前>/` に置きます
- できた型（スキル）は `.claude/skills/<ブランド>-<用途>-<型>/` に置きます。次から同じ種類の物はその型で作ります
- 台本は各スキルのフォルダの `scripts/` にあります（例: `python3 .claude/skills/the-copy/scripts/board.py`）。Python が無い時は、Claude が読んで数えます
- コピー盤は `.the-copy/board/` に置き、`python3 .claude/skills/the-copy/scripts/board.py --dir .the-copy/board --serve 8765` を裏で動かして開きます
- 使う人の API キーやトークンを読み上げない・書き出さない。外に何も送らない
