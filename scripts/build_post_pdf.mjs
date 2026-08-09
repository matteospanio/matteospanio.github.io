#!/usr/bin/env node
/**
 * Renders a blog post to a standalone PDF at public/assets/pdf/posts/<slug>-<version>.pdf.
 *
 * This exists whether or not a DOI is ever minted for the post. Google Scholar's
 * indexing of a personal site is best-effort and slow, and it strongly prefers a
 * crawlable PDF on the same host at `citation_pdf_url`. The PDF is what makes
 * indexing plausible; the DOI is a separate, manual decision.
 *
 * Usage:
 *   npm run build
 *   npx astro preview --port 4321 &
 *   node scripts/build_post_pdf.mjs slow-python 2025 [v1]
 */
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium } from 'playwright';

const [slug, year, version = 'v1'] = process.argv.slice(2);

if (!slug || !year) {
  console.error('usage: node scripts/build_post_pdf.mjs <slug> <year> [version]');
  process.exit(1);
}

const BASE = process.env.PREVIEW_URL ?? 'http://localhost:4321';
const url = `${BASE}/blog/${year}/${slug}/?print=1`;
const outDir = resolve('public/assets/pdf/posts');
const outFile = resolve(outDir, `${slug}-${version}.pdf`);

mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage();

const response = await page.goto(url, { waitUntil: 'networkidle' });
if (!response?.ok()) {
  console.error(`✗ ${url} returned ${response?.status()}`);
  await browser.close();
  process.exit(1);
}

// Open every disclosure so nothing is silently dropped from the PDF.
await page.evaluate(() => {
  for (const d of document.querySelectorAll('details')) d.open = true;
});

const title = await page.title();

await page.pdf({
  path: outFile,
  format: 'A4',
  printBackground: true,
  margin: { top: '18mm', bottom: '20mm', left: '18mm', right: '18mm' },
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: `
    <div style="width:100%;font-size:8px;color:#666;font-family:Georgia,serif;
                padding:0 18mm;display:flex;justify-content:space-between;">
      <span>${url.replace('?print=1', '')}</span>
      <span class="pageNumber"></span>/<span class="totalPages"></span>
    </div>`,
});

await browser.close();
console.log(`✓ ${outFile}\n  title: ${title}`);
