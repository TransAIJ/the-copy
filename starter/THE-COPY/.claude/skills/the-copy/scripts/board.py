#!/usr/bin/env python3
"""THE・COPY のコピー盤を書く・開く台本（標準ライブラリだけ）。

使い方:
  # 作業フォルダに盤を置く（初回）
  python3 board.py --dir .the-copy/board --init
  # 段が進むたびに（--job は JSON ファイルか JSON の文字列。変わった欄だけでよい）
  python3 board.py --dir .the-copy/board --stage 2 --job job-draft.json
  # 盤を http://localhost:8765/ で開けるようにする（止めるまで動くので、裏で動かす）
  python3 board.py --dir .the-copy/board --serve 8765
  # チャット用に、盤と job を1枚の HTML にまとめる
  python3 board.py --inline --job job.json --play --out copy-board.html
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(HERE, "..", "assets", "board", "index.html")

SHIM = """<script id="the-copy-shim">
(function(){
  var INLINE = __JOB__;
  var PLAY = __PLAY__;
  var t0 = Date.now();
  function current(){
    var j = INLINE || window.THE_COPY_JOB || null;
    if (!j) return null;
    if (PLAY && INLINE) {
      var last = Math.max(1, Math.min(7, INLINE.stage || 7));
      var st = Math.min(last, 1 + Math.floor((Date.now() - t0) / 2200));
      j = Object.assign({}, INLINE, {stage: st});
    }
    return j;
  }
  if (location.protocol === 'file:' && !INLINE) {
    setInterval(function(){
      var s = document.createElement('script');
      s.src = 'job.js?t=' + Date.now();
      s.onload = s.onerror = function(){ s.remove(); };
      document.head.appendChild(s);
    }, 1000);
  }
  var original = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u, o){
    var url = String((u && u.url) || u);
    if (/(^|\\/)job\\.json(\\?|$)/.test(url)) {
      var j = current();
      if (j) return Promise.resolve(new Response(JSON.stringify(j), {status: 200, headers: {'content-type': 'application/json'}}));
      if (location.protocol === 'file:' || INLINE) return Promise.resolve(new Response('', {status: 404}));
    }
    return original ? original(u, o) : Promise.reject(new Error('fetch unavailable'));
  };
})();
</script>"""

STAGES = {0: "待つ", 1: "見る", 2: "分ける", 3: "①と②", 4: "埋める", 5: "型にする", 6: "作る", 7: "比べる"}


def load_job_arg(value):
    if value is None:
        return {}
    if os.path.exists(value):
        with open(value, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(value)


def merge(base, extra):
    out = dict(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def inject(html, job, play):
    shim = SHIM.replace("__JOB__", json.dumps(job, ensure_ascii=False) if job else "null")
    shim = shim.replace("__PLAY__", "true" if play else "false")
    html = re.sub(r'<script id="the-copy-shim">.*?</script>', "", html, flags=re.S)
    m = re.search(r"<head[^>]*>", html, flags=re.I)
    if m:
        return html[: m.end()] + "\n" + shim + html[m.end():]
    return shim + html


def write_atomic(path, text):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def check_job(job):
    errs = []
    st = job.get("stage", 0)
    if not isinstance(st, int) or not 0 <= st <= 7:
        errs.append("stage は 0〜7 の整数にしてください")
    if job.get("kind") not in (None, "t2t", "i2i", "v2v"):
        errs.append("kind は t2t・i2i・v2v のどれかにしてください")
    for i, p in enumerate(job.get("parts", [])):
        if p.get("lane") not in ("t2t", "i2i", "v2v"):
            errs.append(f"parts[{i}] の lane は t2t・i2i・v2v のどれかにしてください")
    for k in ("over", "under"):
        v = job.get("meter", {}).get(k, 0)
        if not isinstance(v, (int, float)) or not 0 <= v <= 100:
            errs.append(f"meter.{k} は 0〜100 にしてください")
    return errs


def main():
    ap = argparse.ArgumentParser(description="THE・COPY のコピー盤")
    ap.add_argument("--dir", default=".the-copy/board")
    ap.add_argument("--init", action="store_true", help="盤の HTML を --dir に置く")
    ap.add_argument("--stage", type=int)
    ap.add_argument("--job", help="JSON ファイルか JSON の文字列（変わった欄だけでよい）")
    ap.add_argument("--serve", type=int, metavar="PORT")
    ap.add_argument("--inline", action="store_true", help="盤と job を1枚の HTML にまとめる（チャット用）")
    ap.add_argument("--play", action="store_true", help="--inline の時、1段から順に動かす")
    ap.add_argument("--out", help="--inline の書き出し先（無ければ標準出力）")
    a = ap.parse_args()

    src_html = os.path.join(a.dir, "index.html")
    base_html_path = src_html if os.path.exists(src_html) else ASSET

    if a.inline:
        job = load_job_arg(a.job)
        if a.stage is not None:
            job["stage"] = a.stage
        errs = check_job(job)
        if errs:
            print("× " + " / ".join(errs), file=sys.stderr)
            sys.exit(1)
        with open(base_html_path, encoding="utf-8") as f:
            html = inject(f.read(), job, a.play)
        if a.out:
            os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
            write_atomic(a.out, html)
            print(f"○ {a.out}（{STAGES.get(job.get('stage', 0))}）")
        else:
            sys.stdout.write(html)
        return

    os.makedirs(a.dir, exist_ok=True)
    if a.init or not os.path.exists(src_html):
        with open(ASSET, encoding="utf-8") as f:
            write_atomic(src_html, inject(f.read(), None, False))
        print(f"○ 盤を置きました: {src_html}")

    if a.stage is not None or a.job:
        jp = os.path.join(a.dir, "job.json")
        job = {}
        if os.path.exists(jp):
            with open(jp, encoding="utf-8") as f:
                job = json.load(f)
        job = merge(job, load_job_arg(a.job))
        if a.stage is not None:
            job["stage"] = a.stage
        errs = check_job(job)
        if errs:
            print("× " + " / ".join(errs), file=sys.stderr)
            sys.exit(1)
        text = json.dumps(job, ensure_ascii=False, indent=1)
        write_atomic(jp, text)
        write_atomic(os.path.join(a.dir, "job.js"), "window.THE_COPY_JOB = " + text + ";\n")
        print(f"○ {jp}: {job.get('stage', 0)} {STAGES.get(job.get('stage', 0))}")

    if a.serve:
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def end_headers(self):
                self.send_header("Cache-Control", "no-store")
                super().end_headers()

        handler = functools.partial(Quiet, directory=a.dir)
        with http.server.ThreadingHTTPServer(("127.0.0.1", a.serve), handler) as httpd:
            print(f"○ http://localhost:{a.serve}/ で開けます（止める時は Ctrl+C）", flush=True)
            httpd.serve_forever()


if __name__ == "__main__":
    main()
