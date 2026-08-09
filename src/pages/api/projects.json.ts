import type { APIRoute } from 'astro';
import { abs, allProjects } from '@/lib/content';

export const GET: APIRoute = async () => {
  const projects = await allProjects();
  return new Response(
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        count: projects.length,
        projects: projects.map(({ entry, url, ...rest }) => ({ ...rest, url: abs(url) })),
      },
      null,
      2,
    ),
    { headers: { 'Content-Type': 'application/json; charset=utf-8' } },
  );
};
