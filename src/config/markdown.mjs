import { unified } from '@astrojs/markdown-remark';
import remarkDirective from 'remark-directive';
import remarkMath from 'remark-math';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypeExternalLinks from 'rehype-external-links';
import rehypeKatex from 'rehype-katex';
import rehypeSlug from 'rehype-slug';

import { remarkCallout } from './remark-callout.mjs';

/**
 * Astro 7 renders Markdown with Sätteri by default, which has its own plugin
 * model. We opt back into the unified pipeline because the hard requirements
 * here — KaTeX math, heading anchors, and eventually `rehype-citation` — have
 * no Sätteri equivalents. With ~10 markdown files, Sätteri's build-speed win is
 * worth nothing; correctness is worth everything.
 *
 * This is the single place that decision lives. Swapping back later is one line.
 */
export const markdownProcessor = unified({
  gfm: true, // brings footnotes, tables, strikethrough, autolinks
  smartypants: true,
  remarkPlugins: [remarkDirective, remarkCallout, remarkMath],
  rehypePlugins: [
    [rehypeKatex, { output: 'htmlAndMathml', throwOnError: false, strict: false }],
    rehypeSlug,
    [
      rehypeAutolinkHeadings,
      {
        behavior: 'append',
        properties: { class: 'heading-anchor', ariaHidden: 'true', tabIndex: -1 },
        content: { type: 'text', value: '#' },
      },
    ],
    [rehypeExternalLinks, { target: '_blank', rel: ['noopener', 'noreferrer'] }],
  ],
});
