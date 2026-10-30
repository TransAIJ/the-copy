#!/usr/bin/env python3
"""THE・COPY のダッシュボードを書く・開く台本（標準ライブラリだけ）。

使い方:
  # 作業フォルダにダッシュボードを置く（初回）
  python3 board.py --dir .the-copy/board --init
  # ステップが進むたびに（--job は JSON ファイルか JSON の文字列。変わった欄だけでよい）
  python3 board.py --dir .the-copy/board --stage 2 --job job-draft.json
  # ダッシュボードを http://localhost:8765/ で開けるようにする（裏で動かす。job.json が15分変わらないと自分で止まる）
  python3 board.py --dir .the-copy/board --serve 8765
  # チャット用に、ダッシュボードと job を1枚の HTML にまとめる
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
import threading
import time

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
      // ステップごとの長さ（ミリ秒）。埋めるステップと比べるステップは、文字が打ち終わるまで長めに置く
      var DUR = [0, 2600, 2400, 2400, 4200, 2600, 2400, 4200];
      var last = Math.max(1, Math.min(7, INLINE.stage || 7));
      var el = Date.now() - t0, st = 1;
      while (st < last && el >= DUR[st]) { el -= DUR[st]; st++; }
      j = Object.assign({}, INLINE, {stage: st});
    }
    return j;
  }
  if (location.protocol === 'file:' && !INLINE) {
    // 開いた時に見本が一瞬出ないよう、最初の job.js は読み終えてからダッシュボードを描く
    document.write('<script src="job.js"><\\/script>');
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
    """--job を読む。読めない時は None を返す（呼ぶ側が「×」の文を出して、0 で終える）"""
    if value is None:
        return {}
    try:
        if os.path.exists(value):
            with open(value, encoding="utf-8") as f:
                text = f.read()
        else:
            text = value
        if not text.strip():
            return None
        job = json.loads(text)
    except (OSError, ValueError):
        return None
    return job if isinstance(job, dict) else None


def refuse(msg):
    # 結果は文で返し、終わり方は 0 にする（0 以外で終わると、Claude Code の画面に赤い「Error」が出て、使う人が壊れたと読む）
    print("× " + msg + "（job.json は書き換えていません。直してもう一度動かしてください）")
    sys.exit(0)


BAD_JOB = "--job の中身が読めませんでした。空か、JSON の形になっていません。{\"stage\": 7, \"meter\": {...}} のように渡してください"


def merge(base, extra):
    out = dict(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def safe_json(obj):
    """script 要素の中に置いても閉じられないよう、< > & を \\u 形式にした JSON。"""
    text = json.dumps(obj, ensure_ascii=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def inject(html, job, play):
    shim = SHIM.replace("__JOB__", safe_json(job) if job else "null")
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
    meter = job.get("meter", {}) or {}
    for k in ("over_items", "under_items"):
        v = meter.get(k)
        if v is not None and (not isinstance(v, int) or not 0 <= v <= 6):
            errs.append(f"meter.{k} は 0〜6 の整数（judge.md の6項目のうち当たった数）にしてください")
    v = meter.get("same8")
    if v is not None and (not isinstance(v, int) or v < 0):
        errs.append("meter.same8 は 0 以上の整数（お手本と同じ8文字以上の並びの数）にしてください")
    for k in ("over", "under"):
        v = meter.get(k, 0)
        if not isinstance(v, (int, float)) or not 0 <= v <= 100:
            errs.append(f"meter.{k} は 0〜100 にしてください")
    if job.get("stage") == 7 and "over_items" not in meter:
        errs.append("ステップ7では meter が要ります。judge.md の6項目ずつで、真似しすぎに当たった数（over_items）と真似できていないに当たった数（under_items）を数え、"
                    "同じ8文字以上の並びの数（same8）と一緒に、本文で使う人に伝える数と同じにして "
                    "--stage 7 --job '{\"meter\": {\"over_items\": <数>, \"under_items\": <数>, \"same8\": <数>}}' で書き直してください")
    return errs


def main():
    ap = argparse.ArgumentParser(description="THE・COPY のダッシュボード")
    ap.add_argument("--dir", default=".the-copy/board")
    ap.add_argument("--init", action="store_true", help="ダッシュボードの HTML を --dir に置く")
    ap.add_argument("--stage", type=int)
    ap.add_argument("--job", help="JSON ファイルか JSON の文字列（変わった欄だけでよい）")
    ap.add_argument("--serve", type=int, metavar="PORT")
    ap.add_argument("--idle-exit", type=float, default=15, metavar="MIN",
                    help="--serve の時、job.json がこの分数変わらなければ自分で止まる（0 で止まらない）")
    ap.add_argument("--inline", action="store_true", help="ダッシュボードと job を1枚の HTML にまとめる（チャット用）")
    ap.add_argument("--play", action="store_true", help="--inline の時、ステップ1から順に動かす")
    ap.add_argument("--out", help="--inline の書き出し先（無ければ標準出力）")
    a = ap.parse_args()

    src_html = os.path.join(a.dir, "index.html")
    base_html_path = src_html if os.path.exists(src_html) else ASSET

    if a.inline:
        job = load_job_arg(a.job)
        if job is None:
            refuse(BAD_JOB)
        if a.stage is not None:
            job["stage"] = a.stage
        errs = check_job(job)
        if errs:
            refuse(" / ".join(errs))
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
    if a.init:
        # 0.2 で作った作業フォルダの名前が残っていれば、ここで新しい名前に移す（rename_folders.py を先に動かし忘れた時の網）
        sys.path.insert(0, HERE)
        import rename_folders
        if any(os.path.isdir(d) for d, _ in rename_folders.MOVES):
            rename_folders.main(os.getcwd(), show=False)
    if a.init or not os.path.exists(src_html):
        with open(ASSET, encoding="utf-8") as f:
            write_atomic(src_html, inject(f.read(), None, False))
        print(f"○ ダッシュボードを置きました: {src_html}")

    if a.stage is not None or a.job:
        jp = os.path.join(a.dir, "job.json")
        job = {}
        if os.path.exists(jp):
            with open(jp, encoding="utf-8") as f:
                job = json.load(f)
        prev = job.get("stage", 0)
        extra = load_job_arg(a.job)
        if extra is None:
            refuse(BAD_JOB)
        job = merge(job, extra)
        if a.stage is not None:
            job["stage"] = a.stage
        errs = check_job(job)
        if errs:
            refuse(" / ".join(errs))
        text = json.dumps(job, ensure_ascii=False, indent=1)
        write_atomic(jp, text)
        write_atomic(os.path.join(a.dir, "job.js"), "window.THE_COPY_JOB = " + text + ";\n")
        print(f"○ {jp}: {job.get('stage', 0)} {STAGES.get(job.get('stage', 0))}")
        st = job.get("stage", 0)
        if isinstance(prev, int) and prev >= 1 and st > prev + 1:
            skipped = "・".join(f"{i} {STAGES[i]}" for i in range(prev + 1, st))
            print(f"△ ステップ {skipped} を飛ばしました。ダッシュボードは飛ばしたステップを順に見せてから {st} に進みます。次からは Step を始めるたびに1つずつ書いてください")

    if a.serve:
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def end_headers(self):
                self.send_header("Cache-Control", "no-store")
                super().end_headers()

        handler = functools.partial(Quiet, directory=a.dir)
        with http.server.ThreadingHTTPServer(("127.0.0.1", a.serve), handler) as httpd:
            if a.idle_exit > 0:
                jp = os.path.join(a.dir, "job.json")

                def watch():
                    last = time.time()
                    seen = os.path.getmtime(jp) if os.path.exists(jp) else None
                    while True:
                        time.sleep(5)
                        m = os.path.getmtime(jp) if os.path.exists(jp) else None
                        if m != seen:
                            seen, last = m, time.time()
                        elif time.time() - last > a.idle_exit * 60:
                            httpd.shutdown()
                            return

                threading.Thread(target=watch, daemon=True).start()
            mins = f"{a.idle_exit:g}分" if a.idle_exit > 0 else ""
            tail = f"。job.json が{mins}変わらないと自分で止まります" if mins else ""
            print(f"○ http://localhost:{a.serve}/ で開けます（止める時は Ctrl+C{tail}）", flush=True)
            httpd.serve_forever()


if __name__ == "__main__":
    main()
