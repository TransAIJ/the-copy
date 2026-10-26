#!/usr/bin/env python3
"""音声を手元の CPU で書き起こす（faster-whisper。外に送らない）。

準備（1回だけ）: pip install faster-whisper
使い方: python3 transcribe.py <動画か音声> --out <フォルダ> [--model small] [--lang ja]
出す物: <フォルダ>/transcript.txt（時刻つき）・transcript.srt
長い動画（10分を超える）は、先に ffmpeg で10分ずつに分けてから1つずつ渡すと、メモリを使いすぎません。
"""
import argparse
import os
import sys


def ts(t, srt=False):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",") if srt else f"{m + h * 60:02d}:{s:05.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="ja")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("× faster-whisper がありません。「pip install faster-whisper」を1回だけ実行してください", file=sys.stderr)
        sys.exit(3)
    os.makedirs(a.out, exist_ok=True)
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(a.media, language=a.lang, vad_filter=True)
    txt, srt = [], []
    for i, s in enumerate(segs, 1):
        line = s.text.strip()
        txt.append(f"[{ts(s.start)}] {line}")
        srt.append(f"{i}\n{ts(s.start, True)} --> {ts(s.end, True)}\n{line}\n")
    open(os.path.join(a.out, "transcript.txt"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    open(os.path.join(a.out, "transcript.srt"), "w", encoding="utf-8").write("\n".join(srt))
    print(f"○ {len(txt)}行 → {a.out}/transcript.txt・transcript.srt")


if __name__ == "__main__":
    main()
