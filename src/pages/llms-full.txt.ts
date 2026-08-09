import type { APIRoute } from 'astro';
import { site } from '@/config/site';
import { abs, allNews, allPosts, allProjects, allPublications } from '@/lib/content';

const SEP = '\n\n---\n\n';

/** Full plaintext corpus: about, every post, every abstract, every project. */
export const GET: APIRoute = async () => {
  const [posts, projects, pubs, news] = await Promise.all([
    allPosts(),
    allProjects(),
    allPublications(),
    allNews(),
  ]);

  const blocks: string[] = [];

  blocks.push(
    [
      `# ${site.name}`,
      `URL: ${site.url}`,
      `Role: ${site.jobTitle}`,
      `Affiliation: ${site.affiliation.name}, ${site.affiliation.department}, ${site.affiliation.parent}`,
      `ORCID: ${site.orcid}`,
      '',
      site.tagline,
      '',
      'Research areas:',
      ...site.researchAreas.map((a) => `- ${a}`),
    ].join('\n'),
  );

  for (const p of posts) {
    blocks.push(
      [
        `# ${p.title}`,
        `URL: ${abs(p.url)}`,
        `Date: ${p.date}`,
        `Language: ${p.lang}`,
        `Tags: ${p.tags.join(', ')}`,
        p.doi ? `DOI: ${p.doi}` : '',
        '',
        p.description,
        '',
        (p.entry.body ?? '').trim(),
      ]
        .filter(Boolean)
        .join('\n'),
    );
  }

  for (const p of projects) {
    blocks.push(
      [
        `# Project: ${p.title}`,
        `URL: ${abs(p.url)}`,
        `Status: ${p.status} · ${p.year}`,
        `Stack: ${p.stack.join(', ')}`,
        ...Object.entries(p.links)
          .filter(([, v]) => v)
          .map(([k, v]) => `${k}: ${v}`),
        '',
        p.description,
        '',
        (p.entry.body ?? '').trim(),
      ].join('\n'),
    );
  }

  for (const pub of pubs) {
    blocks.push(
      [
        `# Publication: ${pub.title}`,
        `Authors: ${pub.authors.map((a) => `${a.given} ${a.family}`.trim()).join(', ')}`,
        `Year: ${pub.year}`,
        pub.venue ? `Venue: ${pub.venue}` : '',
        pub.doi ? `DOI: ${pub.doi}` : '',
        `URL: ${abs(`/publications/#${pub.id}`)}`,
        '',
        pub.abstract ?? '(no abstract available)',
      ]
        .filter(Boolean)
        .join('\n'),
    );
  }

  blocks.push(
    ['# News', '', ...news.map((n) => `- ${n.date} (${n.kind}) — ${n.title}`)].join('\n'),
  );

  return new Response(blocks.join(SEP) + '\n', {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
