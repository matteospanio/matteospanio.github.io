import { getCollection, type CollectionEntry } from 'astro:content';

export type Post = CollectionEntry<'blog'>;

/**
 * Jekyll slugified tags and categories by lowercasing and replacing spaces with
 * hyphens; the archive URLs on the live site were generated that way, so the same
 * transform has to survive the migration.
 */
export function slugifyTerm(term: string): string {
  return term
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export async function getPosts(): Promise<Post[]> {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  return posts.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export function postHref(post: Post): string {
  return `/blog/${post.data.date.getFullYear()}/${post.data.slug}/`;
}

/** Maps slug -> { label, posts }, keeping the first-seen human label for display. */
export function groupByTerm(posts: Post[], field: 'tags' | 'categories') {
  const map = new Map<string, { label: string; posts: Post[] }>();

  for (const post of posts) {
    for (const term of post.data[field]) {
      const slug = slugifyTerm(term);
      if (!slug) continue;
      const bucket = map.get(slug) ?? { label: term, posts: [] };
      bucket.posts.push(post);
      map.set(slug, bucket);
    }
  }

  return map;
}

export function groupByYear(posts: Post[]): Map<number, Post[]> {
  const map = new Map<number, Post[]>();
  for (const post of posts) {
    const year = post.data.date.getFullYear();
    map.set(year, [...(map.get(year) ?? []), post]);
  }
  return map;
}

/** ~200 wpm, rounded up; good enough to set expectations, not a promise. */
export function readingMinutes(body: string | undefined): number {
  const words = (body ?? '').trim().split(/\s+/).length;
  return Math.max(1, Math.round(words / 200));
}
