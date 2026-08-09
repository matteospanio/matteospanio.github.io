import type { APIRoute } from 'astro';
import { site } from '@/config/site';
import resume from '@/data/resume.json';
import { abs, allProjects, allPublications } from '@/lib/content';
import { sameAs } from '@/lib/schema';

/**
 * JSON Resume plus research and software extensions, for anything that reads
 * profiles programmatically.
 *
 * There is deliberately no availability / open-to-work block here.
 */
export const GET: APIRoute = async () => {
  const [projects, pubs] = await Promise.all([allProjects(), allPublications()]);

  const tracked = pubs.filter((p) => p.citations !== null);
  const venues = [...new Set(pubs.map((p) => p.venue).filter(Boolean))];

  const payload = {
    ...resume,
    basics: {
      ...resume.basics,
      label: site.jobTitle,
      summary: site.tagline,
      url: site.url,
      profiles: sameAs().map((url) => ({ url })),
    },

    'x-generated': new Date().toISOString().slice(0, 10),
    'x-source': abs('/profile.json'),

    'x-research-areas': site.researchAreas,

    'x-affiliation': {
      lab: site.affiliation.name,
      department: site.affiliation.department,
      institution: site.affiliation.parent,
      url: site.affiliation.url,
      orcid: site.orcid,
    },

    'x-publications': {
      count: pubs.length,
      firstYear: Math.min(...pubs.map((p) => p.year).filter(Boolean)),
      latestYear: Math.max(...pubs.map((p) => p.year)),
      recordedCitations: tracked.reduce((sum, p) => sum + (p.citations ?? 0), 0),
      trackedPapers: tracked.length,
      venues,
      selected: pubs
        .filter((p) => p.selected)
        .map((p) => ({ title: p.title, year: p.year, venue: p.venue, doi: p.doi })),
      all: abs('/api/publications.json'),
    },

    'x-software': projects.map((p) => ({
      name: p.title,
      tagline: p.tagline,
      status: p.status,
      role: p.role,
      year: p.year,
      stack: p.stack,
      links: Object.fromEntries(Object.entries(p.links).filter(([, v]) => v)),
      url: abs(p.url),
    })),

    'x-links': {
      site: site.url,
      cv: abs('/cv/'),
      publications: abs('/publications/'),
      blog: abs('/blog/'),
      contact: abs('/contact/'),
      llms: abs('/llms.txt'),
      llmsFull: abs('/llms-full.txt'),
      feed: abs('/feed.xml'),
    },
  };

  return new Response(JSON.stringify(payload, null, 2), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
};
