import type { APIRoute } from 'astro';
import { site } from '@/config/site';
import { abs, allNews, allPosts, allProjects, allPublications } from '@/lib/content';

/**
 * https://llmstxt.org — a compact map of the site for language models.
 * Kept under ~4 KB: this is the index, `llms-full.txt` is the corpus.
 */
export const GET: APIRoute = async () => {
  const [posts, projects, pubs, news] = await Promise.all([
    allPosts(),
    allProjects(),
    allPublications(),
    allNews(),
  ]);

  const selected = pubs.filter((p) => p.selected);
  const recentPubs = pubs.slice(0, 8);

  const lines: string[] = [
    `# ${site.name}`,
    '',
    `> ${site.tagline}`,
    '',
    `${site.jobTitle} and PhD candidate in Brain, Mind and Computer Science at the ${site.affiliation.parent}, based at the ${site.affiliation.name} (${site.affiliation.department}). ORCID ${site.orcid}.`,
    '',
    'Research areas:',
    ...site.researchAreas.map((a) => `- ${a}`),
    '',
    '## Selected publications',
    '',
    ...selected.map((p) => `- [${p.title}](${abs(`/publications/#${p.id}`)}): ${p.venue ?? ''} ${p.year}.`),
    '',
    '## Recent publications',
    '',
    ...recentPubs
      .filter((p) => !p.selected)
      .map((p) => `- [${p.title}](${abs(`/publications/#${p.id}`)}): ${p.venue ?? ''} ${p.year}.`),
    '',
    '## Projects',
    '',
    ...projects.map((p) => `- [${p.title}](${abs(p.url)}): ${p.tagline}. ${p.stack.slice(0, 4).join(', ')}.`),
    '',
    '## Writing',
    '',
    ...posts.map((p) => `- [${p.title}](${abs(p.url)}): ${p.description}`),
    '',
    '## News',
    '',
    ...news.slice(0, 6).map((n) => `- ${n.date} — ${n.title}`),
    '',
    '## Optional',
    '',
    `- [Full text of everything](${abs('/llms-full.txt')}): every page as plain text.`,
    `- [Machine-readable profile](${abs('/profile.json')}): JSON Resume with research and software metadata.`,
    `- [Publications as JSON](${abs('/api/publications.json')})`,
    `- [CV](${abs('/cv/')})`,
    `- [Contact](${abs('/contact/')})`,
    '',
  ];

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
