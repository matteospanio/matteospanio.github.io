import { chromium } from 'playwright';
const OUT = '/tmp/claude-1000/-home-matteo-Scrivania-Projects-matteospanio-github-io/5d2b4069-8ac0-47e3-a00c-9a5fc6ad3794/scratchpad';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
const errs = []; p.on('pageerror', e => errs.push(String(e)));
await p.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
await p.locator('[data-emap] .stage').scrollIntoViewIfNeeded();
await p.waitForTimeout(2600);
console.log('readout at 0:', await p.locator('#emap-variant-out').textContent());
// scrub to variant 9 (seed 2024, k 5 — highest silhouette)
await p.locator('#emap-variant').fill('9');
await p.waitForTimeout(300);
await p.screenshot({ path: `${OUT}/c-mid.png` });   // mid-morph
console.log('readout at 9:', await p.locator('#emap-variant-out').textContent());
await p.waitForTimeout(1800);
await p.screenshot({ path: `${OUT}/c-settled.png` });
// scrub back
await p.locator('#emap-variant').fill('0');
await p.waitForTimeout(2000);
console.log('back to 0:', await p.locator('#emap-variant-out').textContent());
console.log('pageerrors:', errs.length ? errs : 'none');
await b.close();
