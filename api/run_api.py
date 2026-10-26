#!/usr/bin/env python3
"""上げた THE・COPY のスキルを、Claude API（Messages API＋コードの実行）で1回動かす（任意・従量）。

API の箱はネットに出られず ffmpeg もないので、文章（t2t）と HTML の部品（配置の i2i）までの自動化に使います。
動画（v2v）と写真の層は、作業フォルダ（Claude Code）で動かしてください。

使い方:
  python3 api/run_api.py --source 元.txt --ask "X投稿を1本。わたし.md の中身で" --me 素材棚/わたし.md --out できた物/api
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = os.path.join(ROOT, "api", "skill_ids.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="元の物（文章のファイル）")
    ap.add_argument("--me", help="素材棚/わたし.md")
    ap.add_argument("--ask", required=True, help="何を作るか")
    ap.add_argument("--out", default="api-out")
    ap.add_argument("--model", default=os.environ.get("THE_COPY_MODEL", "claude-opus-5"))
    a = ap.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("× ANTHROPIC_API_KEY がありません。使う人が自分で作った鍵を入れた時だけ動きます", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(IDS):
        print("× 先に api/upload_skills.py でスキルを上げてください", file=sys.stderr)
        sys.exit(2)
    import anthropic

    ids = json.load(open(IDS, encoding="utf-8"))
    client = anthropic.Anthropic()
    text = "元の物:\n" + open(a.source, encoding="utf-8").read()
    if a.me:
        text += "\n\n素材棚/わたし.md:\n" + open(a.me, encoding="utf-8").read()
    text += f"\n\n頼み: {a.ask}\nTHE・COPY の the-copy スキルの手順で、型を作ってから1本作り、元と比べた結果も出してください。質問が要る欄は「（ここに〇〇を入れる）」と残してください。"
    res = client.beta.messages.create(
        model=a.model,
        max_tokens=16000,
        betas=["code-execution-2025-08-25", "server-side-fallback-2026-07-01"],
        fallbacks="default",
        container={"skills": [{"type": "custom", "skill_id": ids[k], "version": "latest"} for k in ("the-copy", "copy-text", "copy-image")]},
        tools=[{"type": "code_execution_20260521", "name": "code_execution"}],
        messages=[{"role": "user", "content": text}],
    )
    if res.stop_reason == "refusal":
        print("× 断られました（言い換えて通さないでください）", file=sys.stderr)
        sys.exit(1)
    os.makedirs(a.out, exist_ok=True)
    body = "\n".join(b.text for b in res.content if getattr(b, "type", "") == "text")
    open(os.path.join(a.out, "answer.md"), "w", encoding="utf-8").write(body)
    for b in res.content:
        content = getattr(b, "content", None)
        for item in getattr(content, "content", []) or []:
            fid = getattr(item, "file_id", None)
            if fid:
                meta = client.files.retrieve_metadata(fid)
                client.files.download(fid).write_to_file(os.path.join(a.out, meta.filename))
                print(f"○ {meta.filename}")
    print(f"○ {a.out}/answer.md（入力 {res.usage.input_tokens}・出力 {res.usage.output_tokens} トークン）")


if __name__ == "__main__":
    main()
