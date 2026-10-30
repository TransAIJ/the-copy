#!/usr/bin/env python3
"""starter/（作業フォルダ版）を skills/ から作り直し、配る zip を dist/ に作る。

使い方: python3 dev/build.py
出すもの:
  starter/THE-COPY/        Code タブで開く作業フォルダ（.claude/skills/ に4本・素材・完成・CLAUDE.md）
  dist/the-copy.zip        claude.ai の「プラグインをアップロード」に使う zip（.claude-plugin/ は plugin.json だけ）
  dist/the-copy-starter.zip  作業フォルダ版の zip
  dist/the-copy-skill.zip    スキル版（1つのスキル。一番上は the-copy/。claude.ai のスキルのアップロードと .claude/skills/ のどちらでも動く）
"""
import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARTER = os.path.join(ROOT, "starter", "THE-COPY")
DIST = os.path.join(ROOT, "dist")
SKIP = {"__pycache__", ".DS_Store", "node_modules"}

CLAUDE_MD = """# THE・COPY の作業フォルダ

このフォルダでは THE・COPY を使います。他人のコンテンツが売れている理由・構造・中身・情報量を真似して、自分の素材で同じ質のものを作る時は、
`.claude/skills/the-copy/SKILL.md` の手順に従ってください。

- 使う人の素材（②）は `素材/` にあります。作る前に `素材/わたし.md` を読みます
- 真似したい他人のものは `素材/お手本/` に置かれます
- 作ったものは `完成/<日付>-<名前>/` に置きます
- 作る前に、先に `python3 .claude/skills/the-copy/scripts/rename_folders.py` を1回動かします（0.2 で作ったフォルダを新しい名前に移す台本。わたし.md と型は消えません。移すものが無ければ何もしません）
- できた型（スキル）は `.claude/skills/<ブランド>-<用途>-<型>/` に置きます。次から同じ種類のものはその型で作ります
- 台本は各スキルのフォルダの `scripts/` にあります（例: `python3 .claude/skills/the-copy/scripts/board.py`）。Python が無い時は、Claude が読んで数えます
- ダッシュボードは `.the-copy/board/` に置き、`python3 .claude/skills/the-copy/scripts/board.py --dir .the-copy/board --init --serve 8765` を裏で動かして開きます。Step 1〜7 を始めるたびに `--stage <ステップ>` で1回ずつ書き、最後に 7 を書いた後もサーバーは止めません
- 使う人の API キーやトークンを読み上げない・書き出さない。外に何も送らない
"""

SHELF_README = """# 素材

THE・COPY が、あなたのもの（②一次情報）を探す場所です。ここにあるものは、あなたの手元だけで使われ、外に送られません。

| 置くもの | 場所 |
|---|---|
| あなたについて（ブランド名・読み手・商品・実績・書き方の癖） | `わたし.md` |
| 実績のスクショ・写真・過去の投稿で「良い」と決めたもの・撮った動画・使ってよい BGM | `自分の素材/` |
| 真似したい他人のもの（本文・スクショ・画面写真・URL の一覧） | `お手本/` |

埋めていない欄は、THE・COPY が作る前に1回だけまとめて質問します。答えはここに書き足すと、次から聞かれません。
"""

ME_MD = """# わたし

## ブランド名（英小文字の短い名前。型の名前の頭に付きます）
例: mybrand

## 自分は誰か（肩書き・何をしている人か・1〜2行）


## 読み手（誰に向けて作るか）


## 商品と価格（言ってよいものだけ）


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


SKILL_DESC = ("THE・COPY（ザ・コピー）。伸びている他人のX投稿・記事・LP・インスタ画像・ショート動画などをお手本に、"
              "売れている理由・構造・中身・情報量を真似し、自分の素材で同じ質のものを作る。"
              "「TTPして」「この投稿の作り方を真似して」「同梱のお手本でX投稿を作って」等の時。")

# スキル版の入口（skills/the-copy/SKILL.md）で、スキルの名前を中のファイルの場所に替える所。1つでも見つからなければ止める
ENTRY_SUBS = [
    ("媒体ごとの手順は、文章が copy-text、画像と画面が copy-image、動画が copy-video のスキルです。",
     "媒体ごとの手順は、文章が `references/text.md`、画像と画面が `references/image.md`、動画が `references/video.md` です。"),
    ("| 媒体 | 見る単位 | スキル |", "| 媒体 | 見る単位 | 手順 |"),
    ("| copy-text |", "| `references/text.md` |"),
    ("| copy-image |", "| `references/image.md` |"),
    ("| copy-video |", "| `references/video.md` |"),
    ("（各スキルの Step 6）", "（各手順の Step 6）"),
    ("- 文章は copy-text、画像と画面は copy-image、動画は copy-video のやり方で作ります",
     "- 文章は `references/text.md`、画像と画面は `references/image.md`、動画は `references/video.md` のやり方で作ります"),
    ("`../copy-text/scripts/text_stats.py --compare`", "`scripts/text_stats.py --compare`"),
]
# references/ の中の別のスキルの名前（スキル版では同じフォルダにある）
REF_SUBS = [
    ("（copy-image の「写真の作り方」）", "（`references/image.md` の「写真の作り方」）"),
    ("`copy-text/scripts/text_stats.py --compare <元> <作ったもの>`", "`scripts/text_stats.py --compare <元> <作ったもの>`"),
]
PART_SUBS = [
    ("the-copy スキル", "入口の SKILL.md"),
    ("the-copy の `references/", "`references/"),
    ("copy-image の①", "`references/image.md` の①"),
    ("copy-text のやり方", "`references/text.md` のやり方"),
]


def body_of(path):
    text = open(path, encoding="utf-8").read()
    assert text.startswith("---\n"), path
    return text.split("\n---\n", 1)[1].lstrip("\n")


def build_skill():
    """skills/ の4本と skill-pack/ から、1つのスキル the-copy/ を dist/skill/ に組む"""
    assert len(SKILL_DESC) <= 200, len(SKILL_DESC)
    out = os.path.join(DIST, "skill", "the-copy")
    if os.path.exists(os.path.dirname(out)):
        shutil.rmtree(os.path.dirname(out))
    os.makedirs(os.path.join(out, "references"))
    os.makedirs(os.path.join(out, "scripts"))
    entry = body_of(os.path.join(ROOT, "skills", "the-copy", "SKILL.md"))
    for old, new in ENTRY_SUBS:
        assert old in entry, old
        entry = entry.replace(old, new)
    quick = open(os.path.join(ROOT, "skill-pack", "QUICK.md"), encoding="utf-8").read()
    mark = "## 使う人の操作は4つだけ"
    assert mark in entry
    entry = entry.replace(mark, quick.rstrip("\n") + "\n\n" + mark, 1)
    head = "---\nname: the-copy\ndescription: \"" + SKILL_DESC + "\"\n---\n\n"
    with open(os.path.join(out, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(head + entry)
    for name, ref in (("copy-text", "text.md"), ("copy-image", "image.md"), ("copy-video", "video.md")):
        part = body_of(os.path.join(ROOT, "skills", name, "SKILL.md"))
        for old, new in PART_SUBS:
            part = part.replace(old, new)
        with open(os.path.join(out, "references", ref), "w", encoding="utf-8") as f:
            f.write(part)
    for name in ("the-copy", "copy-text", "copy-image", "copy-video"):
        for sub in ("references", "scripts"):
            d = os.path.join(ROOT, "skills", name, sub)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if fn in SKIP:
                    continue
                dst = os.path.join(out, sub, fn)
                assert not os.path.exists(dst), dst
                shutil.copy2(os.path.join(d, fn), dst)
                if fn.endswith(".md"):
                    t = open(dst, encoding="utf-8").read()
                    for old, new in REF_SUBS:
                        t = t.replace(old, new)
                    open(dst, "w", encoding="utf-8").write(t)
    copytree(os.path.join(ROOT, "skills", "the-copy", "assets"), os.path.join(out, "assets"))
    copytree(os.path.join(ROOT, "skill-pack", "examples"), os.path.join(out, "examples"))
    shutil.copy2(os.path.join(ROOT, "LICENSE"), os.path.join(out, "LICENSE"))
    # 別のスキルの名前が残っていないか
    left = []
    for r, ds, fs in os.walk(out):
        for fn in fs:
            if fn.endswith(".md"):
                t = open(os.path.join(r, fn), encoding="utf-8").read()
                for w in ("copy-text", "copy-image", "copy-video", "the-copy スキル", "../copy-"):
                    if w in t:
                        left.append(f"{os.path.relpath(os.path.join(r, fn), out)}: {w}")
    if left:
        print("△ 別のスキルの名前が残っています:\n  " + "\n  ".join(left))
    zipdir(os.path.join(DIST, "the-copy-skill.zip"), os.path.join(DIST, "skill"), ["the-copy"])


def main():
    for name in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        copytree(os.path.join(ROOT, "skills", name), os.path.join(STARTER, ".claude", "skills", name))
    files = {
        "CLAUDE.md": CLAUDE_MD,
        os.path.join("素材", "README.md"): SHELF_README,
        os.path.join("素材", "わたし.md"): ME_MD,
        os.path.join("素材", "お手本", ".gitkeep"): "",
        os.path.join("素材", "自分の素材", ".gitkeep"): "",
        os.path.join("完成", ".gitkeep"): "",
        ".gitignore": ".env\n.env.*\n.the-copy/\nnode_modules/\n__pycache__/\n",
    }
    for rel, text in files.items():
        p = os.path.join(STARTER, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
    os.makedirs(DIST, exist_ok=True)
    # claude.ai に上げる zip の .claude-plugin/ は manifest だけにする（公式の文書「Put only the manifest inside .claude-plugin/」）。
    # marketplace.json と icon.png はリポジトリ（マーケットプレイスの入口）にだけ置く
    zipdir(os.path.join(DIST, "the-copy.zip"), ROOT, [os.path.join(".claude-plugin", "plugin.json"), "skills", "README.md", "LICENSE"])
    zipdir(os.path.join(DIST, "the-copy-starter.zip"), os.path.join(ROOT, "starter"), ["THE-COPY"])
    build_skill()
    for z in ("the-copy.zip", "the-copy-starter.zip", "the-copy-skill.zip"):
        print(f"○ dist/{z}（{os.path.getsize(os.path.join(DIST, z)) // 1024} KB）")


if __name__ == "__main__":
    main()
