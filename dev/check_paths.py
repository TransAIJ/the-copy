#!/usr/bin/env python3
"""配る3つの zip の中で、手順の文に書いた道筋が本当にファイルに当たるかを照らす。

使い方: python3 dev/check_paths.py [zip ...]   （省略時は dist/ の3つ。当たらない道筋が1件でもあれば exit 1）

読み方の決まり（Claude Code がスキルの中の道筋を読む時と同じ）:
- スキルの中の .md（SKILL.md と references/ など）に書いた `references/…` `scripts/…` `assets/…` `examples/…` は、
  そのスキルのフォルダ（その .md から上へたどって最初に SKILL.md がある所）から読む
- `../<別のスキル>/…` は、そのスキルのフォルダから1つ上がって読む
- `<このスキルのフォルダ>/…` は、そのスキルのフォルダから読む
- `.claude/…` は作業フォルダ（作業フォルダ版の CLAUDE.md のある所）から読む
- `references/source/…` と `references/decomposition.md` は、使う人が作る型の中の道筋なので照らさない（数だけ出す）
"""
import os
import re
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = r"(?:references|scripts|assets|examples)"
TOKEN = re.compile(r"[^\s`'\"（）()「」、。，|*]*" + DIRS + r"/[^\s`'\"（）()「」、。，|*]*")
TYPE_PATHS = ("references/source", "references/decomposition.md")
SKIP_SCHEMES = ("http://", "https://")


def skill_base(path, top):
    d = os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(d, "SKILL.md")):
            return d
        if os.path.samefile(d, top) or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def project_root(path, top):
    d = os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(d, "CLAUDE.md")):
            return d
        if os.path.samefile(d, top) or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def clean(tok):
    tok = tok.rstrip(".,:;。、）)")
    tok = re.sub(r"^<このスキルのフォルダ>/", "", tok)
    if "<" in tok:  # 置き換える所（<名前> など）から後ろは見ない。手前のフォルダだけ見る
        tok = tok.split("<", 1)[0]
    return tok


def check_tree(top, label):
    bad, ok, typed = [], 0, 0
    for r, _, fs in os.walk(top):
        for fn in fs:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(r, fn)
            base = skill_base(path, top)
            proj = project_root(path, top)
            if base is None and proj is None:
                continue  # スキルの外の説明（README など）は見ない
            rel = os.path.relpath(path, top)
            for no, line in enumerate(open(path, encoding="utf-8"), 1):
                for m in TOKEN.finditer(line):
                    raw = m.group(0)
                    if raw.startswith(SKIP_SCHEMES) or "://" in raw:
                        continue
                    tok = clean(raw)
                    if not tok or not re.search(DIRS + "/", tok):
                        continue
                    if tok.startswith(TYPE_PATHS):
                        typed += 1
                        continue
                    if tok.startswith(".claude/"):
                        if proj is None:
                            bad.append((rel, no, raw, "作業フォルダの外で .claude/ から始まる道筋"))
                            continue
                        target = os.path.join(proj, tok)
                    elif base is None:
                        continue
                    else:
                        target = os.path.normpath(os.path.join(base, tok))
                    if os.path.exists(target.rstrip("/")):
                        ok += 1
                    else:
                        bad.append((rel, no, raw, os.path.relpath(target, top)))
    print(f"[{label}] 当たった道筋 {ok} 件・当たらない道筋 {len(bad)} 件・作る型の中の道筋（照らさない） {typed} 件")
    for rel, no, raw, target in bad:
        print(f"  × {rel}:{no}  {raw}  → {target}")
    return len(bad)


def main(zips):
    total = 0
    for z in zips:
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(z) as f:
                f.extractall(tmp)
            total += check_tree(tmp, os.path.basename(z))
    if total:
        print(f"× 当たらない道筋が {total} 件あります")
        return 1
    print("○ 3つの zip とも、当たらない道筋は 0 件です")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:] or [os.path.join(ROOT, "dist", n) for n in ("the-copy-skill.zip", "the-copy.zip", "the-copy-starter.zip")]
    sys.exit(main(args))
