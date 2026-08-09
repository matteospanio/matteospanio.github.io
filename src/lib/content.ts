import { getCollection } from 'astro:content';
import { site } from '@/config/site';
import type { Publication } from './bib';
import { sortPublications } from './bib';

/**
 * Shared shaping for every machine-readable endpoint (llms.txt, /api/*.json,
 * profile.json) so the JSON, the plaintext and the HTML can never disagree
 * about what exists.
 */

export const abs = (path: string) => new URL(path, site.url).href;

export async function allPosts() {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  return posts
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .map((post) => ({
      entry: post,
      url: `/blog/${post.data.date.getFullYear()}/${post.data.slug}/`,
      title: post.data.title,
      description: post.data.description,
      date: post.data.date.toISOString().slice(0, 10),
      lang: post.data.lang,
      tags: post.data.tags,
      theme: post.data.theme ?? null,
      doi: post.data.citation?.doi ?? null,
    }));
}

export async function allProjects() {
  const projects = await getCollection('projects', ({ data }) => !data.draft);
  return projects
    .sort(
      (a, b) =>
        Number(b.data.featured) - Number(a.data.featured) ||
        a.data.order - b.data.order ||
        b.data.year - a.data.year,
    )
    .map((project) => ({
      entry: project,
      url: `/projects/${project.id.replace(/\/index$/, '')}/`,
      title: project.data.title,
      tagline: project.data.tagline,
      description: project.data.description,
      status: project.data.status,
      role: project.data.role,
      year: project.data.year,
      stack: project.data.stack,
      links: {
        repo: project.data.repo ?? null,
        pypi: project.data.pypi ?? null,
        docs: project.data.docs ?? null,
        huggingface: project.data.hf ?? null,
      },
      paper: project.data.paper ?? null,
    }));
}

export async function allPublications(): Promise<Publication[]> {
  const entries = await getCollection('publications');
  return sortPublications(entries.map((e) => e.data as Publication));
}

export async function allNews() {
  const news = await getCollection('news');
  return news
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .map((item) => ({
      entry: item,
      anchor: `/news/#${item.id}`,
      title: item.data.title,
      date: item.data.date.toISOString().slice(0, 10),
      kind: item.data.kind,
      url: item.data.url ?? null,
    }));
}

export function publicationPayload(pub: Publication) {
  return {
    id: pub.id,
    title: pub.title,
    authors: pub.authors.map((a) => `${a.given} ${a.family}`.trim()),
    year: pub.year,
    venue: pub.venue,
    type: pub.type,
    doi: pub.doi,
    citations: pub.citations,
    selected: pub.selected,
    inPress: pub.inPress,
    abstract: pub.abstract,
    links: Object.fromEntries(Object.entries(pub.links).filter(([, v]) => v)),
    url: abs(`/publications/#${pub.id}`),
  };
}

/** Markdown body with frontmatter stripped, for the plaintext dumps. */
export function stripFrontmatter(body: string | undefined): string {
  return (body ?? '').replace(/^---\n[\s\S]*?\n---\n/, '').trim();
}
