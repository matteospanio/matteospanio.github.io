/**
 * Single source of truth for identity and navigation.
 *
 * Deliberately contains no employment-availability field of any kind: the
 * positioning here is about *what the work is*, never about seeking it.
 */
export const site = {
  url: 'https://matteospanio.github.io',
  name: 'Matteo Spanio',
  handle: 'matteospanio',
  jobTitle: 'AI Research Engineer',

  /** One line, used for the homepage subtitle, meta description and llms.txt. */
  tagline:
    'AI research engineer working on audio, music and multimodal generative models — from cultural-heritage preservation to symbolic music and LLMs.',

  /** Short form for tight surfaces (nav aria-label, OG cards). */
  short: 'AI research engineer · audio, music, multimodal learning',

  affiliation: {
    name: 'Centro di Sonologia Computazionale',
    parent: 'University of Padua',
    department: 'Department of Information Engineering',
    url: 'https://csc.dei.unipd.it/',
  },

  orcid: '0000-0002-2436-7208',
  email: 'spanio@dei.unipd.it',
  locale: 'en',

  researchAreas: [
    'AI for audio cultural heritage preservation',
    'Multimodal and cross-modal generative AI',
    'Symbolic music and large language models',
    'Audio digital signal processing',
    'Music information retrieval',
  ],
} as const;

export const nav = [
  { href: '/', label: 'about' },
  { href: '/publications/', label: 'publications' },
  { href: '/projects/', label: 'projects' },
  { href: '/blog/', label: 'blog' },
  { href: '/news/', label: 'news' },
  { href: '/cv/', label: 'cv' },
  { href: '/contact/', label: 'contact' },
] as const;
