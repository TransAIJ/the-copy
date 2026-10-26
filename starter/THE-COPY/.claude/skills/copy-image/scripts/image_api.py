#!/usr/bin/env python3
"""使う人の API キーで、元の画像を見せて画像を1枚作る（i2i の写真の層・任意）。

既定では使いません。使う人が自分の OPENAI_API_KEY か GEMINI_API_KEY を .env か環境変数に入れた時だけ動きます。
鍵は画面にもファイルにも出しません。--dry-run では送らずに、送る中身（鍵を除く）だけを出します。

使い方:
  python3 image_api.py --provider openai|gemini --image <元の画像> --prompt-file <指示の紙> --out <書き出し先.png> [--model ...] [--dry-run]
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_MODEL = {"openai": "gpt-image-2", "gemini": "gemini-3.1-flash-image-preview"}
KEY_NAME = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


def load_env(path=".env"):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def multipart(fields, files):
    boundary = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (name, data, mime) in files.items():
        out += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode() + data + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return out, f"multipart/form-data; boundary={boundary}"


def send(req):
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:600]
        print(f"× {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["openai", "gemini"], required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model")
    ap.add_argument("--size", default="1024x1536", help="openai の大きさ（例: 1024x1024・1024x1536・1536x1024）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    load_env()
    model = a.model or DEFAULT_MODEL[a.provider]
    prompt = open(a.prompt_file, encoding="utf-8").read().strip()
    img = open(a.image, "rb").read()
    mime = mimetypes.guess_type(a.image)[0] or "image/png"

    if a.dry_run:
        print(json.dumps({"provider": a.provider, "model": model, "image": a.image, "image_bytes": len(img),
                          "prompt_chars": len(prompt), "out": a.out, "key": KEY_NAME[a.provider] + "（送らないので読んでいません）"},
                         ensure_ascii=False, indent=1))
        return

    key = os.environ.get(KEY_NAME[a.provider], "")
    if not key:
        print(f"× {KEY_NAME[a.provider]} がありません。使う人が自分で作った鍵を .env に入れた時だけ動きます（既定は「手で貼る」）", file=sys.stderr)
        sys.exit(2)

    if a.provider == "openai":
        body, ctype = multipart({"model": model, "prompt": prompt, "size": a.size, "n": "1"},
                                {"image[]": (os.path.basename(a.image), img, mime)})
        req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=body,
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": ctype})
        res = send(req)
        b64 = res["data"][0]["b64_json"]
    else:
        payload = {"contents": [{"parts": [{"inline_data": {"mime_type": mime, "data": base64.b64encode(img).decode()}},
                                           {"text": prompt}]}]}
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(payload).encode(), headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        res = send(req)
        parts = res.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        b64 = next((p.get("inlineData", p.get("inline_data", {})).get("data") for p in parts
                    if p.get("inlineData") or p.get("inline_data")), None)
        if not b64:
            print("× 画像が返りませんでした（安全判定で止まった時もこうなります。言い換えて通さないでください）", file=sys.stderr)
            sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"○ {a.out}")


if __name__ == "__main__":
    main()
