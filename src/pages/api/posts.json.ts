import type { APIRoute } from 'astro';
import { abs, allPosts } from '@/lib/content';

export const GET: APIRoute = async () => {
  const posts = await allPosts();
  return new Response(
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        count: posts.length,
        posts: posts.map(({ entry, url, ...rest }) => ({
          ...rest,
          url: abs(url),
          wordCount: (entry.body ?? '').trim().split(/\s+/).length,
        })),
      },
      null,
      2,
    ),
    { headers: { 'Content-Type': 'application/json; charset=utf-8' } },
  );
};
