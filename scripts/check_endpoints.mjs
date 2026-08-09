#!/usr/bin/env node
/**
 * Guards the machine-readable layer against silently emptying out.
 *
 * These files are generated from the content collections, so a loader change or
 * a bad frontmatter edit can leave them syntactically valid but empty — which no
 * other check would notice.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const DIST = resolve(process.argv[2] ?? 'dist');
const errors = [];

const read = (rel) => {
  const path = join(DIST, rel);
  if (!existsSync(path)) {
    errors.push(`${rel}: missing`);
    return null;
  }
  return readFileSync(path, 'utf8');
};

/** JSON endpoints: must parse, and must report a non-zero count. */
for (const [rel, key] of [
  ['api/publications.json', 'publications'],
  ['api/posts.json', 'posts'],
  ['api/projects.json', 'projects'],
]) {
  const raw = read(rel);
  if (!raw) continue;
  try {
    const data = JSON.parse(raw);
    if (!Array.isArray(data[key]) || data[key].length === 0) {
      errors.push(`${rel}: "${key}" is empty`);
    }
  } catch (error) {
    errors.push(`${rel}: invalid JSON — ${error.message}`);
  }
}

const profile = read('profile.json');
if (profile) {
  try {
    const data = JSON.parse(profile);
    if (!data.basics?.name) errors.push('profile.json: basics.name missing');
    if (!data['x-publications']?.count) errors.push('profile.json: x-publications.count is zero');
    // The whole point of the positioning decision: no availability signalling.
    const banned = Object.keys(data).filter((k) => /availability|open.?to.?work|seeking/i.test(k));
    if (banned.length) errors.push(`profile.json: availability fields present (${banned.join(', ')})`);
  } catch (error) {
    errors.push(`profile.json: invalid JSON — ${error.message}`);
  }
}

const llms = read('llms.txt');
if (llms && llms.length < 500) errors.push('llms.txt: suspiciously short');

const llmsFull = read('llms-full.txt');
if (llmsFull && llmsFull.length < 10_000) errors.push('llms-full.txt: suspiciously short');

const feed = read('feed.xml');
if (feed && !feed.includes('<item>')) errors.push('feed.xml: no items');

// No page anywhere may advertise availability.
const AVAILABILITY = /open to work|open-to-work|available for hire|seeking (a )?(new )?(role|position|opportunit)/i;
for (const rel of ['index.html', 'cv/index.html', 'contact/index.html', 'llms.txt']) {
  const raw = read(rel);
  if (raw && AVAILABILITY.test(raw)) errors.push(`${rel}: contains availability language`);
}

if (errors.length) {
  console.error('\n✗ machine-readable layer problems:\n');
  for (const e of errors) console.error(`    ${e}`);
  console.error('');
  process.exit(1);
}

console.log('✓ machine-readable endpoints are populated and clean');
