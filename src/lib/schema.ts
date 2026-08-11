import { site } from '@/config/site';
import socials from '@/data/socials.json';
import type { Publication } from './bib';

/**
 * Structured data for machine readers.
 *
 * Deliberately contains no `seeks`/`Demand` node and no availability property of
 * any kind. What is being communicated is what the work *is*, not that it is
 * wanted.
 */

export function sameAs(): string[] {
  const links: (string | undefined)[] = [
    socials.orcid_id ? `https://orcid.org/${socials.orcid_id}` : undefined,
    socials.scholar_userid ? `https://scholar.google.com/citations?user=${socials.scholar_userid}` : undefined,
    socials.github_username ? `https://github.com/${socials.github_username}` : undefined,
    socials.linkedin_username ? `https://www.linkedin.com/in/${socials.linkedin_username}` : undefined,
    socials.gitlab_username ? `https://gitlab.com/${socials.gitlab_username}` : undefined,
    socials.scopus_id ? `https://www.scopus.com/authid/detail.uri?authorId=${socials.scopus_id}` : undefined,
    socials.research_gate_profile ? `https://www.researchgate.net/profile/${socials.research_gate_profile}` : undefined,
    'https://huggingface.co/csc-unipd',
  ];
  return links.filter((l): l is string => Boolean(l));
}

export const PERSON_ID = `${site.url}/#matteo`;

export function personSchema() {
  return {
    '@type': 'Person',
    '@id': PERSON_ID,
    name: site.name,
    givenName: 'Matteo',
    familyName: 'Spanio',
    jobTitle: site.jobTitle,
    description: site.tagline,
    url: site.url,
    // No `email` here on purpose. It would put the address in plain text in the
    // <head> of every page, which makes obfuscating it on /contact/ pointless.
    // Agents get `url` and `sameAs`; humans get the form.
    identifier: {
      '@type': 'PropertyValue',
      propertyID: 'ORCID',
      value: `https://orcid.org/${site.orcid}`,
    },
    affiliation: {
      '@type': 'Organization',
      name: site.affiliation.name,
      url: site.affiliation.url,
      parentOrganization: { '@type': 'CollegeOrUniversity', name: site.affiliation.parent },
    },
    alumniOf: [
      { '@type': 'CollegeOrUniversity', name: "Ca' Foscari University of Venice" },
      { '@type': 'CollegeOrUniversity', name: 'Conservatorio di Musica Cesare Pollini, Padua' },
    ],
    knowsAbout: [
      ...site.researchAreas,
      'PyTorch',
      'Deep learning',
      'Digital signal processing',
      'Audio restoration',
      'Large language models',
    ],
    knowsLanguage: [
      { '@type': 'Language', name: 'Italian' },
      { '@type': 'Language', name: 'English' },
    ],
    sameAs: sameAs(),
  };
}

export function websiteSchema() {
  return {
    '@type': 'WebSite',
    '@id': `${site.url}/#website`,
    url: site.url,
    name: site.name,
    description: site.tagline,
    inLanguage: 'en',
    publisher: { '@id': PERSON_ID },
  };
}

export function scholarlyArticleSchema(pub: Publication) {
  return {
    '@type': 'ScholarlyArticle',
    headline: pub.title,
    name: pub.title,
    datePublished: String(pub.year),
    inLanguage: pub.lang,
    author: pub.authors.map((a) => ({
      '@type': 'Person',
      name: `${a.given} ${a.family}`.trim(),
      ...(a.isMe ? { '@id': PERSON_ID } : {}),
    })),
    ...(pub.venue ? { publication: pub.venue } : {}),
    ...(pub.abstract ? { abstract: pub.abstract } : {}),
    ...(pub.doi
      ? {
          identifier: { '@type': 'PropertyValue', propertyID: 'DOI', value: pub.doi },
          sameAs: `https://doi.org/${pub.doi}`,
        }
      : {}),
    url: `${site.url}/publications/#${pub.id}`,
  };
}

interface PostSchemaInput {
  title: string;
  description: string;
  date: Date;
  updated?: Date;
  url: string;
  lang: string;
  tags: string[];
  doi?: string;
}

export function postSchema(post: PostSchemaInput) {
  // A post with a DOI is a citable artifact, not just a blog entry.
  const isScholarly = Boolean(post.doi);

  return {
    '@type': isScholarly ? 'ScholarlyArticle' : 'BlogPosting',
    headline: post.title,
    description: post.description,
    datePublished: post.date.toISOString(),
    ...(post.updated ? { dateModified: post.updated.toISOString() } : {}),
    inLanguage: post.lang,
    keywords: post.tags.join(', '),
    author: { '@id': PERSON_ID },
    publisher: { '@id': PERSON_ID },
    mainEntityOfPage: post.url,
    url: post.url,
    isAccessibleForFree: true,
    ...(post.doi
      ? {
          identifier: { '@type': 'PropertyValue', propertyID: 'DOI', value: post.doi },
          sameAs: `https://doi.org/${post.doi}`,
        }
      : {}),
  };
}

export function softwareSchema(p: {
  title: string;
  description: string;
  repo?: string;
  stack: string[];
  url: string;
}) {
  return {
    '@type': 'SoftwareSourceCode',
    name: p.title,
    description: p.description,
    ...(p.repo ? { codeRepository: p.repo } : {}),
    programmingLanguage: p.stack.length ? p.stack[0] : 'Python',
    runtimePlatform: p.stack,
    author: { '@id': PERSON_ID },
    url: p.url,
  };
}

/** Wraps nodes into a single @graph so one script tag carries the whole page. */
export function graph(...nodes: object[]) {
  return { '@context': 'https://schema.org', '@graph': nodes };
}
