#!/usr/bin/env python3
"""0.2 で作った作業フォルダの名前を、0.3 の名前に移す（標準ライブラリだけ）。

  素材棚/          → 素材/
  素材棚/元の物/   → 素材/お手本/
  できた物/        → 完成/

わたし.md・自分の素材・作ったもの・自分の型（.claude/skills/ の中）は消しません。
新しい名前のフォルダがもうある時は、中身を合わせます。同じ名前のファイルがぶつかった時は、
新しい側が空のひな形（わたし.md・README.md・.gitkeep）なら 0.2 の側を残し、そうでなければ
0.2 の側を「<名前>（0.2から）」にして並べます。
CLAUDE.md・素材/README.md・.claude/skills/ の中の Markdown に書かれたフォルダの名前も書き換え、
書き換える前のファイルは .the-copy/before-0.3/ に写して残します。何度動かしても同じ結果になります。

最後に、今の作業フォルダの様子（一番上のファイルとフォルダ、素材/ と 完成/ の中、自分の型、わたし.md が書いてあるか）を出します。
この台本は単独で動かします。ls などをつなぐ必要はありません。

使い方: python3 rename_folders.py [作業フォルダ]   （省くと今いるフォルダ）
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OWN_SKILL = os.path.dirname(HERE)  # このスキルのフォルダ（書き換えない）

MOVES = [("素材棚", "素材"), (os.path.join("素材", "元の物"), os.path.join("素材", "お手本")), ("できた物", "完成")]
TEXT_SUBS = [("素材棚/元の物/", "素材/お手本/"), ("素材棚", "素材"), ("元の物/", "お手本/"), ("できた物/", "完成/"),
             ("`元の物`", "`お手本`"), ("`できた物`", "`完成`"), ("コピー盤", "ダッシュボード"),
             ("できた物", "完成したもの"), ("元の物", "お手本")]
TEMPLATE_NAMES = {".gitkeep", "README.md", "わたし.md"}
# 新しい名前の場所 → 0.2 の時の書き方。ぶつかって名前を変えたファイルを、型の中の参照先にも反映するために使う
OLD_PREFIX = [(os.path.join("素材", "お手本") + os.sep, ["素材棚/元の物/", "素材/元の物/", "元の物/"]), ("素材" + os.sep, ["素材棚/"]), ("完成" + os.sep, ["できた物/"])]
RENAMED = []  # (0.2 の時の書き方の道筋, 並べた先の道筋)


def is_template(path):
    """ひな形のままか（見出しと「例:」の行のほかに何も書いていない）"""
    name = os.path.basename(path)
    if name not in TEMPLATE_NAMES:
        return False
    if name in (".gitkeep", "README.md"):
        return True
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("例:") and not s.startswith("例："):
                return False
    return True


def backup(root, path, log):
    rel = os.path.relpath(path, root)
    dst = os.path.join(root, ".the-copy", "before-0.3", rel)
    if os.path.exists(dst):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(path):
        shutil.copytree(path, dst)
    else:
        shutil.copy2(path, dst)
    log.append(f"  控え: {rel} → .the-copy/before-0.3/{rel}")


def side_name(path):
    stem, ext = os.path.splitext(path)
    cand = f"{stem}（0.2から）{ext}"
    n = 2
    while os.path.exists(cand):
        cand = f"{stem}（0.2から{n}）{ext}"
        n += 1
    return cand


def merge(root, old, new, log):
    for entry in sorted(os.listdir(old)):
        o, t = os.path.join(old, entry), os.path.join(new, entry)
        if not os.path.exists(t):
            shutil.move(o, t)
            log.append(f"  移した: {os.path.relpath(o, root)} → {os.path.relpath(t, root)}")
        elif os.path.isdir(o) and os.path.isdir(t):
            merge(root, o, t, log)
        elif os.path.isfile(o) and os.path.isfile(t) and filecmp.cmp(o, t, shallow=False):
            os.remove(o)
        elif os.path.isfile(o) and os.path.basename(o) in (".gitkeep", "README.md"):
            # どちらも THE・COPY が置いた説明の紙なので、新しい側を残す
            backup(root, o, log)
            os.remove(o)
        elif os.path.isfile(o) and os.path.isfile(t) and is_template(t) and not is_template(o):
            backup(root, t, log)
            os.remove(t)
            shutil.move(o, t)
            log.append(f"  0.2 の {os.path.relpath(o, root)} を残した（新しい側はひな形だった）")
        else:
            s = side_name(t)
            shutil.move(o, s)
            log.append(f"  同じ名前があったので並べた: {os.path.relpath(s, root)}")
            rel_t, rel_s = os.path.relpath(t, root), os.path.relpath(s, root).replace(os.sep, "/")
            for pre, olds in OLD_PREFIX:
                if rel_t.startswith(pre):
                    for op in olds:
                        RENAMED.append((op + rel_t[len(pre):].replace(os.sep, "/"), rel_s))
                    break
    try:
        os.rmdir(old)
    except OSError:
        log.append(f"  △ {os.path.relpath(old, root)} が空にならなかった（中を見てください）")


def text_files(root):
    for rel in ("CLAUDE.md", os.path.join("素材", "README.md")):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            yield p
    skills = os.path.join(root, ".claude", "skills")
    if os.path.isdir(skills):
        for r, ds, fs in os.walk(skills):
            ds[:] = [d for d in ds if d not in ("__pycache__", "node_modules")]
            if os.path.abspath(r) == OWN_SKILL or os.path.abspath(r).startswith(OWN_SKILL + os.sep):
                continue
            for fn in fs:
                if fn.endswith(".md"):
                    yield os.path.join(r, fn)


def listing(path):
    names = []
    for n in sorted(os.listdir(path)):
        names.append(n + "/" if os.path.isdir(os.path.join(path, n)) else n)
    return "  ".join(names) if names else "（空）"


def show_state(root):
    """今の作業フォルダの様子を出す（Claude が ls で見に行かなくて済むように）"""
    print("\n今の作業フォルダ:")
    print(f"  {listing(root)}")
    mat = os.path.join(root, "素材")
    if os.path.isdir(mat):
        print(f"素材/ の中:\n  {listing(mat)}")
    else:
        print("素材/: まだありません（使う時に作ります）")
    done = os.path.join(root, "完成")
    if os.path.isdir(done):
        print(f"完成/ の中（同じ名前のフォルダには上書きしません）:\n  {listing(done)}")
    sk = os.path.join(root, ".claude", "skills")
    own = []
    if os.path.isdir(sk):
        own = [n for n in sorted(os.listdir(sk)) if os.path.isdir(os.path.join(sk, n))
               and n not in ("the-copy", "copy-text", "copy-image", "copy-video")]
    print(f"自分の型（.claude/skills/ の中）: {'  '.join(own) if own else 'まだありません'}")
    me = os.path.join(mat, "わたし.md")
    if not os.path.exists(me):
        me = os.path.join(root, "わたし.md")
    if os.path.exists(me):
        state = "ひな形のままで、まだ書いていません" if is_template(me) else "書いてあります"
        print(f"わたし.md: {os.path.relpath(me, root)} は{state}")
    else:
        print("わたし.md: まだありません")


def main(root=None, show=True):
    root = os.path.abspath(root or (sys.argv[1] if len(sys.argv) > 1 else "."))
    log = []
    RENAMED.clear()
    for old_rel, new_rel in MOVES:
        old, new = os.path.join(root, old_rel), os.path.join(root, new_rel)
        if not os.path.isdir(old):
            continue
        if not os.path.exists(new):
            os.makedirs(os.path.dirname(new), exist_ok=True)
            os.rename(old, new)
            log.append(f"  名前を変えた: {old_rel}/ → {new_rel}/")
        else:
            merge(root, old, new, log)
    for p in text_files(root):
        with open(p, encoding="utf-8", errors="replace") as f:
            t = f.read()
        o = t
        # 並べたファイルを指していた所は、並べた先に書き換える（フォルダの名前の書き換えより先に）
        for a, b in sorted(RENAMED, key=lambda x: -len(x[0])):
            t = t.replace(a, b)
        for a, b in TEXT_SUBS:
            t = t.replace(a, b)
        if t != o:
            backup(root, p, log)
            with open(p, "w", encoding="utf-8") as f:
                f.write(t)
            log.append(f"  フォルダの名前を書き換えた: {os.path.relpath(p, root)}")
    if log:
        print("○ 0.3 の名前に移しました")
        print("\n".join(log))
    else:
        print("○ 移すものはありません（もう 0.3 の名前です）")
    if show:
        show_state(root)


if __name__ == "__main__":
    main()
