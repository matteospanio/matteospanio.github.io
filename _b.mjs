import { chromium } from 'playwright';
const OUT = '/tmp/claude-1000/-home-matteo-Scrivania-Projects-matteospanio-github-io/5d2b4069-8ac0-47e3-a00c-9a5fc6ad3794/scratchpad';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
const errs = []; p.on('pageerror', e => errs.push(String(e)));
await p.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
await p.locator('[data-emap] .stage').scrollIntoViewIfNeeded();
await p.waitForTimeout(2600);

// 1. listen toggle: context created and running inside the gesture
await p.locator('#emap-listen').click();
const audio = await p.evaluate(() => ({
  pressed: document.getElementById('emap-listen').getAttribute('aria-pressed'),
}));
console.log('listen pressed:', audio.pressed);

// 2. click a node → card with walk button
const stage = await p.locator('[data-emap] .stage canvas').boundingBox();
// pick two node screen positions by reading the runtime state through a probe click grid:
// click centre-left cluster first
async function clickAt(fx, fy) {
  await p.mouse.click(stage.x + stage.width * fx, stage.y + stage.height * fy);
  await p.waitForTimeout(500);
}
await clickAt(0.13, 0.30); // heritage cluster area
let card = await p.evaluate(() => {
  const c = document.getElementById('emap-card');
  return { hidden: c.hidden, title: c.querySelector('.card-title').textContent, walkHidden: c.querySelector('.card-walk').hidden };
});
console.log('card after node click:', card);

if (!card.hidden) {
  await p.locator('.card-walk').click();
  await p.waitForTimeout(200);
  console.log('armed meta:', await p.locator('#emap-card .card-meta').textContent());
  // click a far node (engineering, right side)
  await clickAt(0.88, 0.30);
  await p.waitForTimeout(700);
  card = await p.evaluate(() => {
    const c = document.getElementById('emap-card');
    return { hidden: c.hidden, kind: c.querySelector('.card-kind').textContent, title: c.querySelector('.card-title').textContent, meta: c.querySelector('.card-meta').textContent };
  });
  console.log('after second click:', JSON.stringify(card, null, 1));
  await p.screenshot({ path: `${OUT}/b-path.png` });
}
console.log('pageerrors:', errs.length ? errs : 'none');
await b.close();
