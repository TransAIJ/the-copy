#!/usr/bin/env python3
"""カット表から縦の短い動画を書き出す（v2v の Step 6・作業フォルダだけ・任意）。ffmpeg（libass 入り）が要る。

カット表（JSON）の形:
{
  "size": [1080, 1920], "fps": 30,
  "font": "Noto Sans CJK JP",            # Windows は "Meiryo"、Mac は "Hiragino Sans" など
  "telop": {"size": 76, "bottom": 0.30, "outline": 7, "color": "#FFFFFF", "outline_color": "#000000", "chars": 11},
  "bgm": {"file": "素材棚/自分の素材/bgm.mp3", "volume": 0.25},   # 無ければ省く
  "voice": "素材棚/自分の素材/voice.wav",                         # 無ければ省く
  "cuts": [ {"src": "画像か動画", "sec": 1.6, "text": "テロップ", "start": 0} ]
}
使い方: python3 render_short.py <カット表.json> --out <書き出し先.mp4>
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def ass_color(hexstr):
    h = hexstr.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper()


def wrap(text, n):
    out = []
    for line in str(text).split("\n"):
        while len(line) > n:
            out.append(line[:n])
            line = line[n:]
        out.append(line)
    return r"\N".join(x for x in out if x)


def t(sec):
    h, m, s = int(sec // 3600), int(sec % 3600 // 60), sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        print("× ffmpeg が見つかりません。Windows は「winget install Gyan.FFmpeg」、Mac は「brew install ffmpeg」", file=sys.stderr)
        sys.exit(3)
    base = os.path.dirname(os.path.abspath(a.table))
    spec = json.load(open(a.table, encoding="utf-8"))
    W, H = spec.get("size", [1080, 1920])
    fps = spec.get("fps", 30)
    tel = {"size": 76, "bottom": 0.30, "outline": 7, "color": "#FFFFFF", "outline_color": "#000000", "chars": 11, **spec.get("telop", {})}
    cuts = spec["cuts"]
    total = round(sum(c["sec"] for c in cuts), 3)
    out = os.path.abspath(a.out)
    work = os.path.join(os.path.dirname(out), ".render")
    os.makedirs(work, exist_ok=True)

    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: T,{spec.get('font', 'Noto Sans CJK JP')},{tel['size']},{ass_color(tel['color'])},&H00FFFFFF,{ass_color(tel['outline_color'])},&H00000000,-1,0,0,0,100,100,0,0,1,{tel['outline']},0,2,60,60,{int(H * tel['bottom'])},1",
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    pos = 0.0
    for c in cuts:
        if c.get("text"):
            lines.append(f"Dialogue: 0,{t(pos)},{t(pos + c['sec'])},T,,0,0,0,,{wrap(c['text'], tel['chars'])}")
        pos += c["sec"]
    open(os.path.join(work, "telop.ass"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    filt = []
    for i, c in enumerate(cuts):
        src = c["src"] if os.path.isabs(c["src"]) else os.path.join(base, c["src"])
        if os.path.splitext(src)[1].lower() in VIDEO_EXT:
            cmd += ["-ss", str(c.get("start", 0)), "-t", str(c["sec"]), "-i", src]
        else:
            cmd += ["-loop", "1", "-t", str(c["sec"]), "-i", src]
        filt.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={fps},format=yuv420p,trim=duration={c['sec']},setpts=PTS-STARTPTS[v{i}]")
    n = len(cuts)
    filt.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]")
    filt.append("[vc]subtitles=telop.ass[vout]")
    audio_inputs = []
    if spec.get("voice"):
        cmd += ["-i", spec["voice"] if os.path.isabs(spec["voice"]) else os.path.join(base, spec["voice"])]
        audio_inputs.append(f"[{n + len(audio_inputs)}:a]volume=1.0[a{len(audio_inputs)}]")
    if spec.get("bgm", {}).get("file"):
        b = spec["bgm"]
        cmd += ["-stream_loop", "-1", "-i", b["file"] if os.path.isabs(b["file"]) else os.path.join(base, b["file"])]
        audio_inputs.append(f"[{n + len(audio_inputs)}:a]volume={b.get('volume', 0.25)}[a{len(audio_inputs)}]")
    if audio_inputs:
        filt += audio_inputs
        mix = "".join(f"[a{i}]" for i in range(len(audio_inputs)))
        filt.append(f"{mix}amix=inputs={len(audio_inputs)}:duration=longest:normalize=0,atrim=duration={total},loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    else:
        cmd += ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=48000:cl=stereo"]
        filt.append(f"[{n}:a]anull[aout]")
    cmd += ["-filter_complex", ";".join(filt), "-map", "[vout]", "-map", "[aout]", "-t", str(total),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", out]
    p = subprocess.run(cmd, cwd=work)
    if p.returncode:
        sys.exit(p.returncode)
    print(f"○ {out}（{total}秒・カット {n}）")


if __name__ == "__main__":
    main()
