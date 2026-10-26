#!/usr/bin/env node
// THE・COPY: ページを同じ幅・同じ切り方で撮り、文字の計算値を取る（i2i の Step 1 と Step 7）。
// 元のページと自分の作ったページを同じ台本で測り、並べて比べるための物。
//
// 準備（作業フォルダで1回だけ。数分かかります）:
//   npm i -D playwright && npx playwright install chromium
// 使い方:
//   node measure_page.mjs <URL かファイル> --out <フォルダ> [--width 390,1440] [--max 20]
// 出す物（幅ごとに <フォルダ>/<幅>/）:
//   part-01.png …  上から1画面ずつ撮った画像（--max 枚まで）
//   texts.json     文字のある要素の計算値（位置・幅・大きさ・太さ・行間・字間・色・下地・書体・揃え・文字の頭40字）
//   summary.md     ページの高さ、本文の列の幅、よく使う文字の大きさ・太さ・書体・色・下地、角の丸み、ボタン、画像の割合
// ログインの要るページは測りません。元のページの画面写真と測った値は、使う人の手元だけに置き、配りません。
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

let chromium;
try {
  ({ chromium } = createRequire(path.join(process.cwd(), 'package.json'))('playwright'));
} catch {
  console.error('Playwright が見つかりません。作業フォルダで「npm i -D playwright && npx playwright install chromium」を1回だけ実行してください。');
  process.exit(3);
}

const argv = process.argv.slice(2);
const opt = (k, d) => {
  const i = argv.indexOf(`--${k}`);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : d;
};
const url = argv.find((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));
if (!url) {
  console.error('使い方: measure-page.mjs <URL> --out <フォルダ> [--width 390,1440] [--max 20]');
  process.exit(2);
}
// # を含むパスは、そのまま file:// に付けると # から先が無視されるので、必ず pathToFileURL を通す
const target = /^https?:\/\//.test(url) ? url : pathToFileURL(path.resolve(url)).href;
const host = (() => {
  try {
    return new URL(target).hostname || 'file';
  } catch {
    return 'page';
  }
})();
const OUT = path.resolve(opt('out', `/tmp/measure-${host}-${Date.now()}`));
const WIDTHS = opt('width', '390,1440')
  .split(',')
  .map(Number)
  .filter((n) => n > 0);
const MAX = Number(opt('max', 20));
const IPHONE_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch();
try {
  for (const width of WIDTHS) {
    const sp = width < 600;
    const vh = sp ? 844 : 900;
    const dir = path.join(OUT, String(width));
    fs.mkdirSync(dir, { recursive: true });
    const context = await browser.newContext({
      viewport: { width, height: vh },
      deviceScaleFactor: 1,
      isMobile: sp,
      hasTouch: sp,
      ...(sp ? { userAgent: IPHONE_UA } : {}),
    });
    const page = await context.newPage();
    try {
      await page.goto(target, { waitUntil: 'networkidle', timeout: 45000 });
    } catch {
      await page.goto(target, { waitUntil: 'load', timeout: 45000 });
    }
    // 遅れて読む画像を出し切ってから測る
    const height0 = await page.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0, n = 0; y < height0 && n < 80; y += Math.round(vh * 0.8), n += 1) {
      await page.evaluate((yy) => window.scrollTo(0, yy), y);
      await sleep(120);
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(600);

    const data = await page.evaluate(() => {
      const clear = (c) => !c || c === 'transparent' || c === 'rgba(0, 0, 0, 0)';
      const bgOf = (el) => {
        for (let e = el; e; e = e.parentElement) {
          const b = getComputedStyle(e).backgroundColor;
          if (!clear(b)) return b;
        }
        return 'rgb(255, 255, 255)';
      };
      const texts = [];
      const seen = new Set();
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const t = walker.currentNode.textContent.replace(/\s+/g, ' ').trim();
        const el = walker.currentNode.parentElement;
        if (!t || !el || seen.has(el)) continue;
        seen.add(el);
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) continue;
        if (/^(SCRIPT|STYLE|NOSCRIPT)$/.test(el.tagName)) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) continue;
        texts.push({
          y: Math.round(r.top + window.scrollY),
          x: Math.round(r.left),
          w: Math.round(r.width),
          fs: cs.fontSize,
          fw: cs.fontWeight,
          lh: cs.lineHeight,
          ls: cs.letterSpacing,
          color: cs.color,
          bg: bgOf(el),
          ff: cs.fontFamily.split(',')[0].trim(),
          align: cs.textAlign,
          tag: el.tagName.toLowerCase(),
          t: t.slice(0, 40),
        });
      }
      const H = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
      let imgH = 0;
      for (const img of document.images) {
        const r = img.getBoundingClientRect();
        if (r.width >= window.innerWidth * 0.5) imgH += r.height;
      }
      const radii = {};
      for (const el of document.body.querySelectorAll('*')) {
        const b = el.getBoundingClientRect();
        if (b.width < 40 || b.height < 20) continue;
        const r = getComputedStyle(el).borderTopLeftRadius;
        if (r && r !== '0px') radii[r] = (radii[r] || 0) + 1;
      }
      const ctas = [...document.querySelectorAll('a, button, input[type=submit], input[type=button]')]
        .map((el) => {
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          return {
            y: Math.round(r.top + window.scrollY),
            w: Math.round(r.width),
            h: Math.round(r.height),
            bg: cs.backgroundColor,
            color: cs.color,
            fs: cs.fontSize,
            radius: cs.borderTopLeftRadius,
            t: (el.innerText || el.value || '').replace(/\s+/g, ' ').trim().slice(0, 30),
          };
        })
        .filter((c) => c.w >= 120 && c.h >= 36 && !clear(c.bg));
      return { H, W: window.innerWidth, imgH: Math.round(imgH), texts, radii, ctas };
    });

    const parts = Math.min(MAX, Math.ceil(data.H / vh));
    for (let i = 0; i < parts; i += 1) {
      await page.evaluate((yy) => window.scrollTo(0, yy), i * vh);
      await sleep(250);
      await page.screenshot({ path: path.join(dir, `part-${String(i + 1).padStart(2, '0')}.png`) });
    }
    fs.writeFileSync(path.join(dir, 'texts.json'), JSON.stringify(data.texts, null, 1));
    fs.writeFileSync(path.join(dir, 'summary.md'), summarize(target, width, vh, parts, data));
    console.log(`${width}px: 高さ ${data.H}px（${(data.H / vh).toFixed(1)}画面）・文字 ${data.texts.length}件・撮った ${parts}枚 → ${dir}`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log(`\n見る順: 各幅の part-01.png から → summary.md → 細かい値は texts.json。自分の物も同じ幅で撮って並べる`);

function summarize(src, width, vh, parts, d) {
  const body = d.texts.filter((t) => t.t.length >= 12);
  const top = (arr, key, n = 6) => {
    const c = {};
    for (const x of arr) c[x[key]] = (c[x[key]] || 0) + 1;
    return Object.entries(c)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n);
  };
  const line = (pairs) => pairs.map(([k, v]) => `${k}（${v}）`).join(' ／ ') || 'なし';
  const colW = top(
    body.map((t) => ({ w: Math.round(t.w / 10) * 10 })),
    'w',
    3
  );
  const big = [...d.texts]
    .sort((a, b) => parseFloat(b.fs) - parseFloat(a.fs))
    .slice(0, 5)
    .map((t) => `${t.fs}・${t.fw}・${t.ff}・${t.color}／下地 ${t.bg}「${t.t}」`);
  const out = [
    `# ${src}（${width}px）`,
    '',
    `- 高さ: ${d.H}px（${(d.H / vh).toFixed(1)}画面）。撮ったのは上から ${parts}枚`,
    `- 画像が縦を占める割合: ${d.H ? Math.round((d.imgH / d.H) * 100) : 0}%`,
    `- 本文の列の幅（12字以上の文字の幅、10px単位）: ${line(colW.map(([k, v]) => [`${k}px`, v]))}`,
    `- 本文の文字の大きさ: ${line(top(body, 'fs'))}`,
    `- 本文の太さ: ${line(top(body, 'fw', 4))}`,
    `- 本文の行間: ${line(top(body, 'lh', 4))}`,
    `- 書体: ${line(top(d.texts, 'ff', 4))}`,
    `- 文字の色: ${line(top(d.texts, 'color'))}`,
    `- 下地の色: ${line(top(d.texts, 'bg'))}`,
    `- 角の丸み（40×20px以上の箱）: ${line(Object.entries(d.radii).sort((a, b) => b[1] - a[1]).slice(0, 5))}`,
    `- ボタン（幅120・高さ36以上で色の付いた物）: ${d.ctas.length}個`,
    ...d.ctas.slice(0, 6).map((c) => `  - ${(c.y / vh).toFixed(1)}画面目 ${c.w}×${c.h} 地 ${c.bg} 字 ${c.color} ${c.fs} 角 ${c.radius}「${c.t}」`),
    '',
    '## 大きい文字（見出しの候補）',
    ...big.map((b) => `- ${b}`),
    '',
  ];
  return out.join('\n');
}
