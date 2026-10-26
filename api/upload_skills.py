#!/usr/bin/env python3
"""THE・COPY のスキル4本を、使う人の Claude API（Skills API）に上げる（任意・従量）。

既定では使いません。定額の Claude（Pro・Max）で足りる人は不要です。
使う人が自分の Anthropic のコンソールで作った API キーを ANTHROPIC_API_KEY に入れた時だけ動きます。鍵は画面に出しません。

使い方:
  pip install -r api/requirements.txt
  python3 api/upload_skills.py            # 上げて、skill_id を api/skill_ids.json に書く
  python3 api/upload_skills.py --dry-run  # 送らずに、上げるファイルの一覧だけ出す
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = ["the-copy", "copy-text", "copy-image", "copy-video"]
IDS = os.path.join(ROOT, "api", "skill_ids.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        for name in SKILLS:
            d = os.path.join(ROOT, "skills", name)
            files = [os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs]
            print(f"{name}: {len(files)}ファイル")
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("× ANTHROPIC_API_KEY がありません。使う人が自分で作った鍵を入れた時だけ動きます", file=sys.stderr)
        sys.exit(2)
    import anthropic
    from anthropic.lib import files_from_dir

    client = anthropic.Anthropic()
    ids = json.load(open(IDS, encoding="utf-8")) if os.path.exists(IDS) else {}
    for name in SKILLS:
        d = os.path.join(ROOT, "skills", name)
        if name in ids:
            v = client.skills.versions.create(ids[name], files=files_from_dir(d))
            print(f"○ {name}: 新しい版を上げました（{ids[name]}）")
        else:
            s = client.skills.create(display_name=f"THE・COPY {name}", files=files_from_dir(d))
            ids[name] = s.id
            print(f"○ {name}: {s.id}")
    json.dump(ids, open(IDS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"→ {IDS}")


if __name__ == "__main__":
    main()
