import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/**
 * Citation metadata. Every field is optional because a post is citable (BibTeX
 * + APA) whether or not a DOI was ever minted for it — DOIs are hand-picked,
 * one or two a year, never generated automatically.
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
      theme: z
        .enum([
          'cultural-heritage',
          'multimodal',
          'symbolic-music',
          'dsp-tooling',
          'musicology',
          'engineering',
        ])
        .optional(),
      cover: image().optional(),
      draft: z.boolean().default(false),
      math: z.boolean().default(false),
      citation,
      /** BibTeX keys from papers.bib that this post relates to. */
      relatedPapers: z.array(z.string()).default([]),
    }),
});

export const collections = { blog };
