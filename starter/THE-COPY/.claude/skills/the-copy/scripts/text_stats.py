#!/usr/bin/env python3
"""お手本と同じ言い回しを数える台本（本体は copy-text のフォルダの scripts/text_stats.py）。

the-copy のフォルダから `scripts/text_stats.py` で動かしても当たるように、本体へそのまま渡す。
使い方も結果も本体と同じ（python3 scripts/text_stats.py --compare <お手本> <作ったもの>）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.normpath(os.path.join(HERE, "..", "..", "copy-text", "scripts", "text_stats.py"))

if not os.path.isfile(BODY):
    print(f"判定: 数える台本が見つかりませんでした（{BODY}）。お手本と同じ8文字以上の並びは、目で探してください")
    sys.exit(0)
sys.exit(subprocess.call([sys.executable, BODY] + sys.argv[1:]))
