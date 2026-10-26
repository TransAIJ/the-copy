#!/usr/bin/env python3
"""動画の場面を切り出して数える（v2v の Step 1 と Step 7）。ffmpeg と ffprobe が要る。

場面の種類と順・場面の数を見るための道具です。秒数などの値は型に写しません。

測る物: 長さ・縦横・カットの変わり目（各カットの長さ）・無音の区間・音量（LUFS）・カットごとの1枚。
使い方:
  python3 video_measure.py <動画> --out <フォルダ> [--scene 0.3] [--noise -35] [--min-silence 0.3]
出す物: <フォルダ>/cuts.json・summary.md・frames/cut-001.jpg …
大きい動画でもメモリに全部を読まず、ffmpeg に流して測ります。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def need(tool):
    if not shutil.which(tool):
        print(f"× {tool} が見つかりません。Windows は「winget install Gyan.FFmpeg」、Mac は「brew install ffmpeg」で入れてください", file=sys.stderr)
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scene", type=float, default=0.3, help="カットの変わり目とみなす差（0〜1。小さいほど細かく切る）")
    ap.add_argument("--noise", type=float, default=-35, help="無音とみなす音量 dB")
    ap.add_argument("--min-silence", type=float, default=0.3, help="無音とみなす長さ（秒）")
    ap.add_argument("--max-frames", type=int, default=120)
    a = ap.parse_args()
    need("ffmpeg"), need("ffprobe")
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)

    _, out, _ = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                     "-of", "json", a.video])
    info = json.loads(out or "{}")
    dur = float(info.get("format", {}).get("duration", 0) or 0)
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    w, h = v.get("width", 0), v.get("height", 0)
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = round(float(num) / float(den or 1), 2) if float(den or 1) else 0

    _, _, err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-an",
                     "-vf", f"scale=320:-2,select='gt(scene,{a.scene})',showinfo", "-f", "null", "-"])
    cuts = [0.0] + [float(x) for x in re.findall(r"pts_time:([0-9.]+)", err)]
    cuts = sorted(set(round(c, 2) for c in cuts if c < dur or not dur))
    bounds = cuts + [round(dur, 2)]
    shots = [{"no": i + 1, "start": bounds[i], "end": bounds[i + 1], "sec": round(bounds[i + 1] - bounds[i], 2)}
             for i in range(len(bounds) - 1) if bounds[i + 1] > bounds[i]]

    silences, lufs, lra = [], None, None
    if has_audio:
        _, _, err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vn",
                         "-af", f"silencedetect=noise={a.noise}dB:d={a.min_silence}", "-f", "null", "-"])
        starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", err)]
        ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
        silences = [{"start": round(s, 2), "end": round(e, 2), "sec": round(e - s, 2)} for s, e in zip(starts, ends)]
        _, _, err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
        m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)
        lufs = float(m[-1]) if m else None
        m = re.findall(r"LRA:\s+([0-9.]+) LU", err)
        lra = float(m[-1]) if m else None

    for s in shots[: a.max_frames]:
        t = min(s["start"] + min(0.3, s["sec"] / 2), max(0, dur - 0.05))
        path = os.path.join(a.out, "frames", f"cut-{s['no']:03d}.jpg")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video,
             "-frames:v", "1", "-vf", "scale=540:-2", "-q:v", "4", path])
        s["frame"] = os.path.relpath(path, a.out)

    secs = [s["sec"] for s in shots] or [0]
    data = {"file": os.path.basename(a.video), "duration": round(dur, 2), "width": w, "height": h, "fps": fps,
            "cuts": len(shots), "cut_sec_avg": round(sum(secs) / len(secs), 2), "cut_sec_min": min(secs), "cut_sec_max": max(secs),
            "first_cut_sec": secs[0], "silences": silences, "silence_total_sec": round(sum(x["sec"] for x in silences), 2),
            "lufs_integrated": lufs, "lra": lra, "shots": shots}
    with open(os.path.join(a.out, "cuts.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    md = [f"# {data['file']}", "",
          f"- 長さ {data['duration']}秒・{w}×{h}・{fps}fps",
          f"- カット {data['cuts']}個。平均 {data['cut_sec_avg']}秒（最短 {data['cut_sec_min']}・最長 {data['cut_sec_max']}）。最初のカット {data['first_cut_sec']}秒",
          f"- 無音（{a.noise}dB 以下が {a.min_silence}秒以上）{len(silences)}か所・合計 {data['silence_total_sec']}秒",
          f"- 音量 {lufs} LUFS（幅 {lra} LU）" if has_audio else "- 音声なし", "",
          "| カット | 始まり | 長さ | 1枚 |", "|---|---|---|---|"]
    md += [f"| {s['no']} | {s['start']} | {s['sec']} | {s.get('frame', '')} |" for s in shots]
    with open(os.path.join(a.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md[:6]))
    print(f"\n→ {a.out}/summary.md・cuts.json・frames/")


if __name__ == "__main__":
    main()
