import { defineCollection } from 'astro:content';
import { file, glob } from 'astro/loaders';
import { z } from 'astro/zod';

import { parseBib } from './lib/bib';

const THEMES = [
  'cultural-heritage',
  'multimodal',
  'symbolic-music',
  'dsp-tooling',
  'musicology',
  'engineering',
] as const;

/**
 * Citation metadata. Every field is optional because a post is citable (BibTeX +
 * APA) whether or not a DOI was ever minted for it — DOIs here are hand-picked,
 * one or two a year, and never generated automatically.
 */
const citation = z
  .object({
    doi: z.string().optional(), // this version
    conceptDoi: z.string().optional(), // all versions of this post
    zenodoRecord: z.number().optional(),
    version: z.string().default('v1'),
    pdf: z.string().optional(),
  })
  .optional();

const blog = defineCollection({
  loader: glob({ base: './src/content/blog', pattern: '**/index.{md,mdx}' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      description: z.string(),
      date: z.coerce.date(),
      updated: z.coerce.date().optional(),
      /**
       * The exact legacy path segment, case included. Jekyll preserved filename
       * case and GitHub Pages serves case-sensitively, so `DSP-il-suono-in-digitale`
       * must stay capitalised or every inbound link to it breaks.
       */
      slug: z.string(),
      lang: z.enum(['en', 'it']).default('en'),
      categories: z.array(z.string()).default([]),
      tags: z.array(z.string()).default([]),
      theme: z.enum(THEMES).optional(),
      cover: image().optional(),
      draft: z.boolean().default(false),
      math: z.boolean().default(false),
      citation,
      /** BibTeX keys from papers.bib that this post relates to. */
      relatedPapers: z.array(z.string()).default([]),
    }),
});

const news = defineCollection({
  loader: glob({ base: './src/content/news', pattern: '**/*.md' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    kind: z.enum(['conference', 'release', 'paper', 'talk', 'award', 'misc']).default('misc'),
    url: z.url().optional(),
    pinned: z.boolean().default(false),
  }),
});

const projects = defineCollection({
  loader: glob({ base: './src/content/projects', pattern: '**/index.{md,mdx}' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      tagline: z.string(),
      description: z.string(),
      status: z.enum(['active', 'maintained', 'archived', 'research']),
      role: z.string(),
      year: z.number(),
      endYear: z.number().optional(),
      theme: z.enum(THEMES).optional(),
      stack: z.array(z.string()).default([]),
      repo: z.url().optional(),
      pypi: z.url().optional(),
      docs: z.url().optional(),
      hf: z.url().optional(),
      /** A BibTeX key from papers.bib. */
      paper: z.string().optional(),
      cover: image().optional(),
      featured: z.boolean().default(false),
      order: z.number().default(100),
      draft: z.boolean().default(false),
    }),
});

/**
 * papers.bib becomes a first-class, Zod-validated, HMR-aware collection: editing
 * the bibliography hot-reloads /publications/ in dev.
 */
const publications = defineCollection({
  loader: file('./src/data/papers.bib', {
    // `file()` keys array output by the `id` field, which every entry carries.
    parser: (text) => parseBib(text) as unknown as Record<string, unknown>[],
  }),
  schema: z.object({
    id: z.string(),
    type: z.string(),
    title: z.string(),
    authors: z.array(
      z.object({
        given: z.string(),
        family: z.string(),
        isMe: z.boolean(),
        url: z.string().optional(),
      }),
    ),
    year: z.number(),
    venue: z.string().nullable(),
    venueKey: z.string().nullable(),
    abbr: z.string().nullable(),
    doi: z.string().nullable(),
    links: z.record(z.string(), z.string().optional()),
    preview: z.string().nullable(),
    selected: z.boolean(),
    scholarId: z.string().nullable(),
    abstract: z.string().nullable(),
    lang: z.string(),
    note: z.string().nullable(),
    inPress: z.boolean(),
    citations: z.number().nullable(),
    raw: z.string(),
  }),
});

export const collections = { blog, news, projects, publications };
