import { chromium } from 'playwright';
const OUT = '/tmp/claude-1000/-home-matteo-Scrivania-Projects-matteospanio-github-io/5d2b4069-8ac0-47e3-a00c-9a5fc6ad3794/scratchpad';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
const errs = []; p.on('pageerror', e => errs.push(String(e).slice(0, 200)));
await p.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
await p.locator('[data-emap] .stage').scrollIntoViewIfNeeded();
await p.waitForTimeout(2200);
console.log('gate label:', (await p.locator('#emap-search-load').textContent()).trim());
await p.locator('#emap-search-load').click();
// wait for the input to appear (model loaded) — up to 3 minutes
try {
  await p.locator('#emap-search-input').waitFor({ state: 'visible', timeout: 180000 });
  console.log('model loaded, input visible');
} catch {
  console.log('TIMEOUT — status:', await p.locator('#emap-search-status').textContent());
  await b.close(); process.exit(1);
}
await p.locator('#emap-search-input').fill('restoring damaged magnetic tape recordings');
await p.waitForTimeout(2500);
const results = await p.locator('#emap-search-results li').allTextContents();
console.log('results for tape query:'); results.forEach(r => console.log('  ', r.trim()));
await p.screenshot({ path: `${OUT}/d-search.png` });
// second query: taste
await p.locator('#emap-search-input').fill('music generated from taste of food');
await p.waitForTimeout(2000);
console.log('results for taste query:');
(await p.locator('#emap-search-results li').allTextContents()).forEach(r => console.log('  ', r.trim()));
// click first result → card opens
await p.locator('#emap-search-results button').first().click();
await p.waitForTimeout(600);
console.log('card:', await p.locator('#emap-card .card-title').textContent());
console.log('pageerrors:', errs.length ? errs : 'none');
await b.close();
