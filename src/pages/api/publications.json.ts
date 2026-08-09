import type { APIRoute } from 'astro';
import { allPublications, publicationPayload } from '@/lib/content';

export const GET: APIRoute = async () => {
  const pubs = await allPublications();
  return new Response(
    JSON.stringify(
      { generatedAt: new Date().toISOString(), count: pubs.length, publications: pubs.map(publicationPayload) },
      null,
      2,
    ),
    { headers: { 'Content-Type': 'application/json; charset=utf-8' } },
  );
};
