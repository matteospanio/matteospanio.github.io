// @ts-check
import { defineConfig, fontProviders } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import expressiveCode from 'astro-expressive-code';

import { markdownProcessor } from './src/config/markdown.mjs';

export default defineConfig({
  site: 'https://matteospanio.github.io',
  // No `base`: this is a GitHub user site, served from the domain root.
  trailingSlash: 'always',
  build: { format: 'directory' },

  markdown: {
    processor: markdownProcessor,
    // Expressive Code owns highlighting; letting Shiki also run would double-wrap.
    syntaxHighlight: false,
  },

  integrations: [
    // Must come before mdx() so .mdx code blocks get the same treatment.
    expressiveCode({
      themes: ['github-dark-default', 'github-light'],
      // Map both themes onto the site's own light/dark attribute so a single
      // `data-theme` on <html> drives page chrome and code blocks together.
      themeCssSelector: (theme) => `[data-theme='${theme.type}']`,
      styleOverrides: {
        borderRadius: '0',
        borderColor: 'var(--rule)',
        codeFontFamily: 'var(--font-mono)',
        uiFontFamily: 'var(--font-mono)',
        codeFontSize: '0.85rem',
      },
    }),
    mdx(),
    sitemap({ filter: (page) => !page.includes('/404') }),
  ],

  fonts: [
    {
      provider: fontProviders.google(),
      name: 'JetBrains Mono',
      cssVariable: '--font-mono-src',
      weights: [400, 500, 700],
      styles: ['normal'],
      // latin-ext carries Rodà, Niccolò, Spohr — all present in the bibliography.
      subsets: ['latin', 'latin-ext'],
      fallbacks: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
    },
    {
      provider: fontProviders.google(),
      name: 'Inter',
      cssVariable: '--font-sans-src',
      weights: ['400 700'],
      styles: ['normal', 'italic'],
      subsets: ['latin', 'latin-ext'],
      fallbacks: ['system-ui', 'sans-serif'],
    },
  ],
});
