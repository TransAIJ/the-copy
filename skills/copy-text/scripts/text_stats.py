#!/usr/bin/env python3
"""文章の①形式を数える・元と作った物の重なりを数える（標準ライブラリだけ）。

使い方:
  python3 text_stats.py <文章.txt>                     # 数える
  python3 text_stats.py --compare <元.txt> <作った.txt> [--n 8] [--allow "Claude Code,無料"]
"""
import argparse
import json
import re
import sys
import unicodedata

BULLET = re.compile(r"^\s*([・\-•▶■□◆◇●○✅☑︎✔️→]|[①-⑳]|\d+[.)．、]|[（(]\d+[)）])")
SENT_END = re.compile(r"(?<=[。！？!?])|\n")


def sentences(text):
    out = []
    for s in SENT_END.split(text):
        s = s.strip()
        if s:
            out.append(s)
    return out


def ending(s):
    s = re.sub(r"[。！？!?\s」』）)]+$", "", s)
    for e in sorted(("ます", "ました", "です", "でした", "ません", "ください", "だ", "だった", "た", "る", "い", "ない"), key=len, reverse=True):
        if s.endswith(e):
            return e
    if not s:
        return "空"
    ch = s[-1]
    name = unicodedata.name(ch, "")
    if "CJK" in name or "KATAKANA" in name or ch.isalnum():
        return "体言止め・その他"
    return "記号"


def measure(text):
    lines = text.split("\n")
    nonblank = [l for l in lines if l.strip()]
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    sents = sentences(text)
    lens = [len(s) for s in sents]
    ends = {}
    for s in sents:
        e = ending(s)
        ends[e] = ends.get(e, 0) + 1
    return {
        "文字数（空白と改行を除く）": len(re.sub(r"\s", "", text)),
        "行数（空行を除く）": len(nonblank),
        "空行の数": sum(1 for l in lines if not l.strip()),
        "段落の数": len(paras),
        "文の数": len(sents),
        "1文目の字数": lens[0] if lens else 0,
        "文の字数（平均）": round(sum(lens) / len(lens), 1) if lens else 0,
        "文の字数（最短・最長）": [min(lens), max(lens)] if lens else [0, 0],
        "1行の字数（平均）": round(sum(len(l.strip()) for l in nonblank) / len(nonblank), 1) if nonblank else 0,
        "箇条の行": sum(1 for l in nonblank if BULLET.match(l)),
        "数字を含む文": sum(1 for s in sents if re.search(r"[0-9０-９]", s)),
        "かぎ括弧": text.count("「"),
        "ハッシュタグ": len(re.findall(r"[#＃][^\s#＃]+", text)),
        "URL": len(re.findall(r"https?://\S+", text)),
        "語尾": dict(sorted(ends.items(), key=lambda x: -x[1])),
    }


def norm(t):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t))


def overlaps(src, out, n, allow):
    s, o = norm(src), norm(out)
    for a in allow:
        a = norm(a)
        if a:
            s = s.replace(a, "\0")
            o = o.replace(a, "\1")
    grams = {s[i:i + n] for i in range(len(s) - n + 1)}
    spans, i = [], 0
    while i <= len(o) - n:
        if o[i:i + n] in grams:
            j = i + n
            while j < len(o) and o[i:j + 1] in s:
                j += 1
            spans.append(o[i:j])
            i = j
        else:
            i += 1
    return spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--n", type=int, default=8, help="同じとみなす並びの長さ（既定 8 文字）")
    ap.add_argument("--allow", default="", help="重なりから除く言葉（カンマ区切り。商品名・一般的な言い方）")
    a = ap.parse_args()
    read = lambda p: open(p, encoding="utf-8").read()
    if not a.compare:
        print(json.dumps(measure(read(a.files[0])), ensure_ascii=False, indent=1))
        return
    if len(a.files) != 2:
        print("--compare には <元> <作った物> の2つを渡してください", file=sys.stderr)
        sys.exit(2)
    src, out = read(a.files[0]), read(a.files[1])
    ms, mo = measure(src), measure(out)
    print("| 項目 | 元 | 作った物 |\n|---|---|---|")
    for k in ms:
        print(f"| {k} | {json.dumps(ms[k], ensure_ascii=False)} | {json.dumps(mo[k], ensure_ascii=False)} |")
    allow = [x for x in a.allow.split(",") if x.strip()]
    spans = overlaps(src, out, a.n, allow)
    print(f"\n元と同じ{a.n}文字以上の並び: {len(spans)}か所")
    for sp in spans:
        print(f"- {sp}")
    sys.exit(1 if spans else 0)


if __name__ == "__main__":
    main()
