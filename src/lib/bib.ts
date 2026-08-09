import { parse as parseBibTeX } from '@retorquere/bibtex-parser';

import citationsData from '@/data/citations.json';
import coauthorsData from '@/data/coauthors.json';
import venuesData from '@/data/venues.json';

export interface Author {
  given: string;
  family: string;
  /** True for Matteo, so the card can bold him without string-matching in templates. */
  isMe: boolean;
  url?: string;
}

export interface PublicationLinks {
  pdf?: string;
  poster?: string;
  arxiv?: string;
  code?: string;
  html?: string;
  url?: string;
  website?: string;
  doi?: string;
}

export interface Publication {
  id: string;
  type: string;
  title: string;
  authors: Author[];
  year: number;
  venue: string | null;
  venueKey: string | null;
  abbr: string | null;
  doi: string | null;
  links: PublicationLinks;
  preview: string | null;
  selected: boolean;
  scholarId: string | null;
  abstract: string | null;
  lang: string;
  note: string | null;
  /** True when `note` says the paper is accepted but not yet out. */
  inPress: boolean;
  /** null (not "0") when we simply have no measurement for this paper. */
  citations: number | null;
  raw: string;
}

const ME = /^spanio$/i;

/**
 * BibTeX braces are a formatting instruction, not content: `{LilyPond}` only means
 * "do not case-fold this". Strip them for display but keep the text.
 */
function clean(value: unknown): string {
  if (typeof value !== 'string') return '';
  return value
    .replace(/[{}]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

const coauthorUrls = new Map<string, string>(
  Object.entries(coauthorsData as Record<string, { url?: string }[] | { url?: string }>).flatMap(
    ([family, entries]) => {
      const list = Array.isArray(entries) ? entries : [entries];
      return list
        .filter((e) => e && typeof e.url === 'string' && e.url)
        .map((e) => [family.toLowerCase(), e.url as string] as [string, string]);
    },
  ),
);

function toAuthor(raw: { firstName?: string; lastName?: string; name?: string }): Author {
  // Some entries write `author = {Sergio Canazza}` rather than `{Canazza, Sergio}`.
  let given = clean(raw.firstName);
  let family = clean(raw.lastName);

  if (!family && raw.name) {
    const parts = clean(raw.name).split(' ');
    family = parts.pop() ?? '';
    given = parts.join(' ');
  }

  return {
    given,
    family,
    isMe: ME.test(family),
    url: coauthorUrls.get(family.toLowerCase()),
  };
}

/** Bare filenames in the bib mean "a PDF I host"; full URLs mean "somebody else hosts it". */
function resolveAsset(value: unknown, base: string): string | undefined {
  const v = clean(value);
  if (!v) return undefined;
  return /^https?:\/\//.test(v) ? v : `${base}${v}`;
}

const citations = citationsData as {
  papers: Record<string, { citations: number | null; title: string; year: string }>;
};

/** Titles differ in case and punctuation across sources; compare on letters and digits only. */
function titleKey(title: string): string {
  return title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]/g, '');
}

const citationsByTitle = new Map(
  Object.values(citations.papers).map((p) => [titleKey(p.title), p.citations]),
);

/**
 * Only 7 of 17 entries carry a `google_scholar_id`, so an id-only lookup silently
 * leaves ten papers — including every 2026 one — without a count. Fall back to a
 * normalised title match before giving up.
 */
function lookupCitations(scholarId: string | null, title: string): number | null {
  if (scholarId) {
    const direct = citations.papers[scholarId];
    if (direct && typeof direct.citations === 'number') return direct.citations;
  }
  const byTitle = citationsByTitle.get(titleKey(title));
  return typeof byTitle === 'number' ? byTitle : null;
}

const venues = venuesData as Record<string, { label: string; kind: string; color: string }>;

/** Entries without an `abbr` still deserve a badge: infer one from the entry shape. */
function inferVenueKey(abbr: string | null, type: string, venue: string | null): string | null {
  if (abbr && venues[abbr]) return abbr;
  if (type === 'thesis') return 'Thesis';
  if (venue && /arxiv/i.test(venue)) return 'arXiv';
  if (type === 'misc') return 'Score';
  return null;
}

export function parseBib(text: string): Publication[] {
  const bib = parseBibTeX(text.replace(/^---\s*\n---\s*\n/, ''), {
    // Titles in this bibliography are already cased the way they should display.
    // Leaving this on lowercases proper nouns ("Contaminazioni Jazz" -> "contaminazioni jazz").
    sentenceCase: false,
    verbatimFields: [/^doi$/, /^url$/, /^html$/, /^pdf$/, /^code$/, /^website$/, /^poster$/],
  });

  return bib.entries.map((entry): Publication => {
    const f = entry.fields as Record<string, any>;
    const title = clean(f.title);
    const abbr = clean(f.abbr) || null;
    const type = entry.type;
    const venue = clean(f.journal || f.booktitle || f.howpublished) || null;
    const scholarId = clean(f.google_scholar_id) || null;
    const doi = clean(f.doi) || null;
    const note = clean(f.note) || null;
    const arxiv = clean(f.arxiv);

    const authorsRaw = Array.isArray(f.author) ? f.author : f.author ? [f.author] : [];

    return {
      id: entry.key,
      type,
      title,
      authors: authorsRaw.map(toAuthor),
      year: Number(clean(f.year)) || 0,
      venue,
      venueKey: inferVenueKey(abbr, type, venue),
      abbr,
      doi,
      links: {
        pdf: resolveAsset(f.pdf, '/assets/pdf/'),
        poster: resolveAsset(f.poster, '/assets/pdf/'),
        arxiv: arxiv ? `https://arxiv.org/abs/${arxiv}` : undefined,
        code: clean(f.code) || undefined,
        html: clean(f.html) || undefined,
        url: clean(f.url) || undefined,
        website: clean(f.website) || undefined,
        doi: doi ? `https://doi.org/${doi}` : undefined,
      },
      preview: clean(f.preview) || null,
      selected: clean(f.selected) === 'true',
      scholarId,
      abstract: clean(f.abstract) || null,
      lang: clean(f.language) || 'en',
      note,
      inPress: /accepted for publication/i.test(note ?? ''),
      citations: lookupCitations(scholarId, title),
      raw: entry.input ?? '',
    };
  });
}

/** Newest first; within a year, `selected` papers lead. */
export function sortPublications(pubs: Publication[]): Publication[] {
  return [...pubs].sort(
    (a, b) => b.year - a.year || Number(b.selected) - Number(a.selected) || a.title.localeCompare(b.title),
  );
}

export function groupByYear(pubs: Publication[]): [number, Publication[]][] {
  const map = new Map<number, Publication[]>();
  for (const p of sortPublications(pubs)) {
    const list = map.get(p.year) ?? [];
    list.push(p);
    map.set(p.year, list);
  }
  return [...map.entries()].sort((a, b) => b[0] - a[0]);
}
