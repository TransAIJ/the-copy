#!/usr/bin/env python3
"""starter/（作業フォルダ版）を skills/ から作り直し、配る zip を dist/ に作る。

使い方: python3 dev/build.py
出す物:
  starter/THE-COPY/        Code タブで開く作業フォルダ（.claude/skills/ に4本・素材棚・できた物・CLAUDE.md）
  dist/the-copy.zip        claude.ai の「プラグインをアップロード」に使う zip
  dist/the-copy-starter.zip  作業フォルダ版の zip
"""
import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARTER = os.path.join(ROOT, "starter", "THE-COPY")
DIST = os.path.join(ROOT, "dist")
SKIP = {"__pycache__", ".DS_Store", "node_modules"}

CLAUDE_MD = """# THE・COPY の作業フォルダ

このフォルダでは THE・COPY を使います。他人のコンテンツが売れている理由・構造・中身・情報量を写して、自分の素材で同じ質の物を作る時は、
`.claude/skills/the-copy/SKILL.md` の手順に従ってください。

- 使う人の素材（②）は `素材棚/` にあります。作る前に `素材棚/わたし.md` を読みます
- 写したい他人の物は `素材棚/元の物/` に置かれます
- 作った物は `できた物/<日付>-<名前>/` に置きます
- できた型（スキル）は `.claude/skills/<ブランド>-<用途>-<型>/` に置きます。次から同じ種類の物はその型で作ります
- 台本は各スキルのフォルダの `scripts/` にあります（例: `python3 .claude/skills/the-copy/scripts/board.py`）。Python が無い時は、Claude が読んで数えます
- コピー盤は `.the-copy/board/` に置き、`python3 .claude/skills/the-copy/scripts/board.py --dir .the-copy/board --init --serve 8765` を裏で動かして開きます。Step 1〜7 を始めるたびに `--stage <段>` で1回ずつ書き、最後に 7 を書いた後もサーバーは止めません
- 使う人の API キーやトークンを読み上げない・書き出さない。外に何も送らない
"""

SHELF_README = """# 素材棚

THE・COPY が、あなたの物（②一次情報）を探す場所です。ここにある物は、あなたの手元だけで使われ、外に送られません。

| 置く物 | 場所 |
|---|---|
| あなたについて（ブランド名・読み手・商品・実績・書き方の癖） | `わたし.md` |
| 実績のスクショ・写真・過去の投稿で「良い」と決めた物・撮った動画・使ってよい BGM | `自分の素材/` |
| 写したい他人の物（本文・スクショ・画面写真・URL の一覧） | `元の物/` |

埋めていない欄は、THE・COPY が作る前に1回だけまとめて質問します。答えはここに書き足すと、次から聞かれません。
"""

ME_MD = """# わたし

## ブランド名（英小文字の短い名前。型の名前の頭に付きます）
例: mybrand

## 自分は誰か（肩書き・何をしている人か・1〜2行）


## 読み手（誰に向けて作るか）


## 商品と価格（言ってよい物だけ）


## 実績（言ってよい数字と、その根拠）


## 最近の出来事（判断が変わったこと・やめたこと・始めたこと）


## 導線（プロフィール・LINE・LP・申込の URL）


## 書き方の癖（語尾・一人称・使う言葉）


## 見た目の決まり（ブランドの色・書体。空なら、読みやすさの既定で作ります）


## 使わない言葉・言ってはいけないこと

"""


def copytree(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP))


def zipdir(zpath, base, items, prefix=""):
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for item in items:
            p = os.path.join(base, item)
            if os.path.isfile(p):
                z.write(p, os.path.join(prefix, item))
                continue
            for r, ds, fs in os.walk(p):
                ds[:] = [d for d in ds if d not in SKIP]
                for f in fs:
                    if f in SKIP:
                        continue
                    full = os.path.join(r, f)
                    z.write(full, os.path.join(prefix, os.path.relpath(full, base)))


def main():
    for name in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        copytree(os.path.join(ROOT, "skills", name), os.path.join(STARTER, ".claude", "skills", name))
    files = {
        "CLAUDE.md": CLAUDE_MD,
        os.path.join("素材棚", "README.md"): SHELF_README,
        os.path.join("素材棚", "わたし.md"): ME_MD,
        os.path.join("素材棚", "元の物", ".gitkeep"): "",
        os.path.join("素材棚", "自分の素材", ".gitkeep"): "",
        os.path.join("できた物", ".gitkeep"): "",
        ".gitignore": ".env\n.env.*\n.the-copy/\nnode_modules/\n__pycache__/\n",
    }
    for rel, text in files.items():
        p = os.path.join(STARTER, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
    os.makedirs(DIST, exist_ok=True)
    zipdir(os.path.join(DIST, "the-copy.zip"), ROOT, [".claude-plugin", "skills", "README.md", "LICENSE"])
    zipdir(os.path.join(DIST, "the-copy-starter.zip"), os.path.join(ROOT, "starter"), ["THE-COPY"])
    for z in ("the-copy.zip", "the-copy-starter.zip"):
        print(f"○ dist/{z}（{os.path.getsize(os.path.join(DIST, z)) // 1024} KB）")


if __name__ == "__main__":
    main()
