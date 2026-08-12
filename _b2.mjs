import { chromium } from 'playwright';
const OUT = '/tmp/claude-1000/-home-matteo-Scrivania-Projects-matteospanio-github-io/5d2b4069-8ac0-47e3-a00c-9a5fc6ad3794/scratchpad';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
const errs = []; p.on('pageerror', e => errs.push(String(e)));
await p.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
await p.locator('[data-emap] .stage').scrollIntoViewIfNeeded();
await p.waitForTimeout(2600);
await p.locator('#emap-listen').click(); // audio on

// Recompute node screen positions with the component's own layout math.
const pos = await p.evaluate(() => {
  const { nodes } = JSON.parse(document.getElementById('emap-data').textContent);
  const c = document.getElementById('emap');
  const r = c.getBoundingClientRect();
  const xs = nodes.map(n => n.x), ys = nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const w = r.width, h = r.height;
  const pad = Math.max(20, Math.min(54, w * 0.055));
  const fit = Math.min((w - pad * 2) / (maxX - minX), (h - pad * 2) / (maxY - minY));
  const offX = (w - (maxX - minX) * fit) / 2, offY = (h - (maxY - minY) * fit) / 2;
  return nodes.map(n => ({ id: n.id, theme: n.theme, x: r.x + offX + (n.x - minX) * fit, y: r.y + offY + (n.y - minY) * fit }));
});
const a = pos.find(n => n.theme === 'cultural-heritage');
const z = pos.find(n => n.theme === 'engineering');
console.log('clicking', a.id, '->', z.id);
await p.mouse.click(a.x, a.y); await p.waitForTimeout(600);
let card = await p.evaluate(() => { const c = document.getElementById('emap-card'); return { hidden: c.hidden, title: c.querySelector('.card-title').textContent }; });
console.log('card A:', card);
await p.locator('.card-walk').click(); await p.waitForTimeout(200);
console.log('armed:', await p.locator('#emap-card .card-meta').textContent());
// after openCard the camera zoomed to 1.55 around A — recompute? Camera transform: kT=1.55, txT = w/2 - bx*kT. Node Z moved. Read via same math + camera state… simplest: dblclick empty corner resets? dblclick = reset() closes card AND clears arm. Instead: compute Z's new position: screen = z_base * k + tx. bx = offX + (z.x-minX)*fit (canvas-relative). tx = w/2 - bx_A*k.
const zNew = await p.evaluate(({ aId, zId }) => {
  const { nodes } = JSON.parse(document.getElementById('emap-data').textContent);
  const c = document.getElementById('emap');
  const r = c.getBoundingClientRect();
  const xs = nodes.map(n => n.x), ys = nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const w = r.width, h = r.height;
  const pad = Math.max(20, Math.min(54, w * 0.055));
  const fit = Math.min((w - pad * 2) / (maxX - minX), (h - pad * 2) / (maxY - minY));
  const offX = (w - (maxX - minX) * fit) / 2, offY = (h - (maxY - minY) * fit) / 2;
  const base = id => { const n = nodes.find(n => n.id === id); return { bx: offX + (n.x - minX) * fit, by: offY + (n.y - minY) * fit }; };
  const A = base(aId), Z = base(zId);
  const k = 1.55, tx = w / 2 - A.bx * k, ty = h / 2 - A.by * k;
  return { x: r.x + Z.bx * k + tx, y: r.y + Z.by * k + ty, inX: Z.bx * k + tx > 0 && Z.bx * k + tx < w, inY: Z.by * k + ty > 0 && Z.by * k + ty < h };
}, { aId: a.id, zId: z.id });
console.log('Z after zoom:', zNew);
if (zNew.inX && zNew.inY) {
  await p.mouse.click(zNew.x, zNew.y);
} else {
  console.log('Z off-stage after zoom — clicking nearest visible instead not implemented');
}
await p.waitForTimeout(900);
card = await p.evaluate(() => { const c = document.getElementById('emap-card'); return { kind: c.querySelector('.card-kind').textContent, title: c.querySelector('.card-title').textContent, meta: c.querySelector('.card-meta').textContent }; });
console.log('walk result:', JSON.stringify(card));
await p.waitForTimeout(1200);
await p.screenshot({ path: `${OUT}/b-path.png` });
console.log('pageerrors:', errs.length ? errs : 'none');
await b.close();
