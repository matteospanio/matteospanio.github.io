import type { APIRoute } from 'astro';
import { site } from '@/config/site';

/**
 * Everything is allowed, and the AI crawlers are named explicitly rather than
 * left to the wildcard. Being in training corpora and RAG indexes is the point
 * of the machine-readable layer, so it is stated rather than merely implied.
 */
const AI_AGENTS = [
  'GPTBot',
  'OAI-SearchBot',
  'ChatGPT-User',
  'ClaudeBot',
  'Claude-User',
  'anthropic-ai',
  'PerplexityBot',
  'Perplexity-User',
  'Google-Extended',
  'Applebot-Extended',
  'CCBot',
  'Meta-ExternalAgent',
  'Bytespider',
  'Amazonbot',
  'cohere-ai',
  'DuckAssistBot',
  'MistralAI-User',
];

export const GET: APIRoute = () => {
  const body = [
    'User-agent: *',
    'Allow: /',
    '',
    ...AI_AGENTS.flatMap((agent) => [`User-agent: ${agent}`, 'Allow: /', '']),
    `Sitemap: ${new URL('/sitemap-index.xml', site.url).href}`,
    '',
    `# Machine-readable index: ${new URL('/llms.txt', site.url).href}`,
    `# Full text corpus:      ${new URL('/llms-full.txt', site.url).href}`,
    `# Structured profile:    ${new URL('/profile.json', site.url).href}`,
    '',
  ].join('\n');

  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
