import { chromium } from 'playwright';
const OUT = '/tmp/claude-1000/-home-matteo-Scrivania-Projects-matteospanio-github-io/5d2b4069-8ac0-47e3-a00c-9a5fc6ad3794/scratchpad';
const b = await chromium.launch();
// metrics
for (const [w, h] of [[1440, 900], [1366, 768]]) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(400);
  console.log(w + 'x' + h, await p.evaluate(() => {
    const box = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return { y: Math.round(r.y + scrollY), x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height) }; };
    return { stage: box('[data-emap] .stage'), legend: box('[data-emap] .legend'), figure: box('[data-emap]'), selWork: box('.columns section:first-child .label'), news: box('.columns section:last-child .label') };
  }));
  await p.close();
}
// pubs first-year
const p2 = await b.newPage({ viewport: { width: 1440, height: 900 } });
await p2.goto('http://localhost:4321/publications/', { waitUntil: 'networkidle' });
console.log('pubs firstYear y:', await p2.evaluate(() => Math.round(document.querySelector('.year').getBoundingClientRect().y + scrollY)));
await p2.close();
// shots
async function shot(name, o) {
  const ctx = await b.newContext({ viewport: { width: o.w || 1440, height: o.h || 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  if (o.theme) await p.addInitScript(t => localStorage.setItem('theme', t), o.theme);
  await p.goto('http://localhost:4321' + (o.url || '/'), { waitUntil: 'networkidle' });
  if (o.scrollTo) await p.locator(o.scrollTo).first().scrollIntoViewIfNeeded();
  await p.waitForTimeout(o.settle || 2200);
  await p.screenshot({ path: `${OUT}/${name}.png` });
  await ctx.close();
}
await shot('a-fold-1366', { w: 1366, h: 768 });
await shot('a-rail-1440', { scrollTo: '[data-emap]' });
await shot('a-light-map', { theme: 'light', scrollTo: '[data-emap]' });
await shot('a-cv', { url: '/cv/', settle: 500 });
await shot('a-cols', { scrollTo: '.columns', settle: 500 });
await b.close(); console.log('shots done');
