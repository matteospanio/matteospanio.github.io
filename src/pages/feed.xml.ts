import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import { site } from '@/config/site';

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf(),
  );

  return rss({
    title: `${site.name} — ${site.jobTitle}`,
    description: site.tagline,
    site: context.site ?? site.url,
    trailingSlash: true,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.date,
      link: `/blog/${post.data.date.getFullYear()}/${post.data.slug}/`,
      categories: [...post.data.tags, ...post.data.categories],
      // Name only: an <author> email is one more plain-text copy to harvest.
      author: site.name,
    })),
    customData: `<language>en</language>`,
  });
}
