#!/usr/bin/env node
/**
 * Turns "don't break inbound links" from a hope into a build condition.
 *
 * Every path the Jekyll site served must still resolve in ./dist — either as a
 * real page or as a redirect stub. Run after `astro build`.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const DIST = resolve(process.argv[2] ?? 'dist');
const LIST = resolve('scripts/legacy_urls.txt');

const paths = readFileSync(LIST, 'utf8')
  .split('\n')
  .map((line) => line.trim())
  .filter((line) => line && !line.startsWith('#'));

/** A URL resolves if dist has the file itself or its directory index. */
function resolves(urlPath) {
  const rel = urlPath.replace(/^\//, '');
  const candidates = urlPath.endsWith('/') || rel === ''
    ? [join(DIST, rel, 'index.html')]
    : [join(DIST, rel), join(DIST, rel, 'index.html')];
  return candidates.some(existsSync);
}

const missing = paths.filter((p) => !resolves(p));

if (missing.length > 0) {
  console.error(`\n✗ ${missing.length} legacy URL(s) no longer resolve in ${DIST}:\n`);
  for (const p of missing) console.error(`    ${p}`);
  console.error(
    '\nAdd a page or an entry to src/config/redirects.ts. Do not delete lines from' +
      '\nscripts/legacy_urls.txt — those URLs are already out in the world.\n',
  );
  process.exit(1);
}

console.log(`✓ all ${paths.length} legacy URLs still resolve`);
