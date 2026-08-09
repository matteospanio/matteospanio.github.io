import { site } from '@/config/site';

/**
 * Citation strings for blog posts.
 *
 * Every post gets a citation block whether or not a DOI was ever minted for it:
 * a `@misc` entry with an author, a title, a year and a URL is perfectly
 * citable. The DOI, when it exists, is an upgrade rather than a precondition.
 */

export interface CiteInput {
  title: string;
  date: Date;
  updated?: Date;
  url: string;
  version?: string;
  doi?: string;
  /** Zenodo "all versions" DOI: what a reader should normally cite. */
  conceptDoi?: string;
}

const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

/** Escape the characters BibTeX treats as syntax, and protect proper-noun casing. */
function bibtexTitle(title: string): string {
  return title.replace(/([A-Z][A-Za-z]*[A-Z][A-Za-z]*)/g, '{$1}');
}

export function bibtexKey(input: CiteInput): string {
  const slug = input.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
    .slice(0, 18);
  return `spanio${input.date.getFullYear()}${slug}`;
}

export function toBibTeX(input: CiteInput): string {
  const year = input.date.getFullYear();
  const month = MONTHS[input.date.getMonth()];
  // Cite the concept DOI by default: it always resolves to the latest version.
  const doi = input.conceptDoi ?? input.doi;

  const fields: [string, string][] = [
    ['author', '{Spanio, Matteo}'],
    ['title', `{${bibtexTitle(input.title)}}`],
    ['year', `{${year}}`],
    ['month', month],
  ];

  if (input.version) fields.push(['version', `{${input.version}}`]);
  if (doi) {
    fields.push(['publisher', '{Zenodo}']);
    fields.push(['doi', `{${doi}}`]);
    fields.push(['url', `{https://doi.org/${doi}}`]);
    fields.push(['howpublished', `{\\url{${input.url}}}`]);
  } else {
    fields.push(['howpublished', `{Blog post, \\url{${input.url}}}`]);
    fields.push(['url', `{${input.url}}`]);
  }

  const width = Math.max(...fields.map(([k]) => k.length));
  const body = fields
    .map(([key, value]) => `  ${key.padEnd(width)} = ${value}`)
    .join(',\n');

  return `@misc{${bibtexKey(input)},\n${body}\n}`;
}

export function toAPA(input: CiteInput): string {
  const date = input.date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
  const [day, month, year] = date.split(' ');
  const doi = input.conceptDoi ?? input.doi;
  const where = doi ? `https://doi.org/${doi}` : input.url;

  return `Spanio, M. (${year}, ${month} ${day}). ${input.title}. ${site.name}. ${where}`;
}

/**
 * Google Scholar's Highwire Press tags. Emitted only when a DOI exists — Scholar
 * treats these as a claim that the page is a formal publication, and tagging
 * ordinary blog posts this way is how a site gets ignored.
 */
export function highwireTags(input: CiteInput & { pdf?: string; keywords?: string[] }) {
  if (!input.doi) return [];

  const d = input.date;
  const pad = (n: number) => String(n).padStart(2, '0');

  const tags: [string, string][] = [
    ['citation_title', input.title],
    // One tag per author, "Family, Given" — never comma-joined into one tag.
    ['citation_author', 'Spanio, Matteo'],
    ['citation_author_institution', `${site.affiliation.department}, ${site.affiliation.parent}`],
    ['citation_author_orcid', `https://orcid.org/${site.orcid}`],
    ['citation_publication_date', `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())}`],
    ['citation_online_date', `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())}`],
    ['citation_doi', input.doi],
    ['citation_abstract_html_url', input.url],
    // Not a journal: claiming one Scholar cannot verify is the fastest way to be dropped.
    ['citation_technical_report_institution', `${site.affiliation.name}, ${site.affiliation.parent}`],
    ['citation_language', 'en'],
    ['citation_fulltext_world_readable', ''],
  ];

  if (input.pdf) tags.push(['citation_pdf_url', new URL(input.pdf, site.url).href]);
  if (input.keywords?.length) tags.push(['citation_keywords', input.keywords.join('; ')]);

  return tags;
}
