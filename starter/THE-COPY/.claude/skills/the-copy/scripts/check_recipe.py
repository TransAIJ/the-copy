#!/usr/bin/env python3
"""THE・COPY で作った型（SKILL.md）を点検する。「○」で終わるまで直す。

使い方: python3 check_recipe.py <型のフォルダ>/SKILL.md
"""
import os
import re
import sys

REQUIRED = ["元にしたコンテンツ", "部品と工程", "①写す形式", "②一次情報", "作る手順", "確かめ方"]
PLACEHOLDER = re.compile(r"^(|-|—|\.\.\.|…|TODO|TBD|未定|適宜|必要に応じて|<[^>]*>)$", re.I)
VAGUE = re.compile(r"(な感じ|雰囲気で|テイストで)")


def table_rows(lines):
    rows = []
    for l in lines:
        if not re.match(r"^\s*\|", l) or re.match(r"^\s*\|\s*:?-{2,}", l):
            continue
        rows.append([c.strip() for c in l.strip().strip("|").split("|")])
    return rows


def main():
    if len(sys.argv) < 2:
        print("使い方: check_recipe.py <SKILL.md>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    d = os.path.dirname(os.path.abspath(path))
    text = open(path, encoding="utf-8").read()
    errors = []

    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    name = ""
    if fm:
        m = re.search(r"^name:\s*(.+?)\s*$", fm.group(1), re.M)
        name = m.group(1) if m else ""
    if not re.match(r"^[a-z0-9]+-[a-z0-9]+-[a-z0-9]+$", name):
        errors.append(f"名前「{name}」が「ブランド-用途-型」の3段になっていません。各段は英小文字と数字だけで、区切りは - です")
    if os.path.basename(d) != name:
        errors.append(f"フォルダ名「{os.path.basename(d)}」と名前「{name}」が違います")

    sections, cur = {}, None
    for line in text.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            sections[cur] = []
            continue
        if cur:
            sections[cur].append(line)
    for s in REQUIRED:
        if s not in sections:
            errors.append(f"見出し「## {s}」がありません")
        elif not "".join(sections[s]).strip():
            errors.append(f"「{s}」が空です")

    rows = table_rows(sections.get("部品と工程", []))
    head = rows.pop(0) if rows else []
    conv = next((i for i, h in enumerate(head) if "変換" in h), -1)
    if conv < 0:
        errors.append("部品表に「変換」の列がありません")
    if not rows:
        errors.append("部品表に部品が1つもありません")
    ids = []
    for r in rows:
        ids.append(r[0])
        c = (r[conv] if 0 <= conv < len(r) else "").lower()
        if c not in ("t2t", "i2i", "v2v"):
            errors.append(f"部品 {r[0]} の変換が「{c}」です。t2t・i2i・v2v のどれか1つにし、混じるなら部品を分けてください")

    form = "\n".join(sections.get("①写す形式", []))
    for i in ids:
        if i and i not in form:
            errors.append(f"①写す形式に部品 {i} の値がありません")
    if VAGUE.search(form):
        errors.append("①に「〜な感じ」「雰囲気で」「テイストで」があります。測った値か順番で書いてください")

    info = table_rows(sections.get("②一次情報", []))
    ih = info.pop(0) if info else []
    kind = next((i for i, h in enumerate(ih) if "種類" in h), -1)
    where = next((i for i, h in enumerate(ih) if "在りか" in h), -1)
    if where < 0:
        errors.append("②の表に「在りか」の列がありません")
    if not info:
        errors.append("②の欄が1つもありません。自分の素材が要らない物は、THE・COPY で作る物か見直してください")
    for r in info:
        nm = r[0] or "(名前なし)"
        w = r[where] if 0 <= where < len(r) else ""
        k = r[kind] if 0 <= kind < len(r) else ""
        if PLACEHOLDER.match(w):
            errors.append(f"②「{nm}」の在りかが空です")
        elif re.match(r"^(使う人|依頼者|ユーザー|本人)に聞く。?$", w):
            errors.append(f"②「{nm}」の在りかが「聞く」だけです。探した場所と、無い時に何を聞くかを書いてください")
        if kind >= 0 and k not in ("データ", "取り方"):
            errors.append(f"②「{nm}」の種類は「データ」か「取り方」にしてください（今: {k or '空'}）")
        if k == "データ":
            for ref in re.findall(r"`([^`]+)`", w):
                if not os.path.exists(os.path.join(d, ref)) and not os.path.exists(ref):
                    errors.append(f"②「{nm}」のデータ {ref} が見つかりません")

    src = os.path.join(d, "references", "source")
    if not os.path.isdir(src) or not os.listdir(src):
        errors.append("references/source/ に元の物（原文・画像・場面）がありません")

    if errors:
        print(f"× {len(errors)}件")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    print(f"○ 部品{len(ids)}つ・②の欄{len(info)}つ。すべて在りかがあります")


if __name__ == "__main__":
    main()
