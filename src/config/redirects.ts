/**
 * Every URL the Jekyll site served that this site does not reproduce one-for-one.
 * Astro emits meta-refresh pages for these in a static build, which is all GitHub
 * Pages can do — but it keeps inbound links and search results alive.
 *
 * `scripts/legacy_urls.txt` is the regression net: CI asserts every legacy path
 * still resolves in ./dist, so deleting an entry here fails the build.
 */
export const redirects: Record<string, string> = {
  // --- sitemap: @astrojs/sitemap emits an index, the old site emitted a flat file
  '/sitemap.xml': '/sitemap-index.xml',

  // --- news detail pages become anchors on the news timeline.
  // One-paragraph updates do not deserve their own page, but the URLs must live.
  '/news/announcement_2/': '/news/#announcement_2',
  '/news/ann_4/': '/news/#ann_4',
  '/news/aes2024NY/': '/news/#aes2024NY',
  '/news/aixia2024/': '/news/#aixia2024',
  '/news/hf2025/': '/news/#hf2025',
  '/news/dafx2025/': '/news/#dafx2025',
  '/news/hf2026-lilybert/': '/news/#hf2026-lilybert',
  '/news/2026-ItalIA/': '/news/#2026-ItalIA',

  // --- renamed project pages
  '/projects/3_project/': '/projects/spam-analyzer/',
  '/projects/4_project/': '/projects/ml-project-template/',

  // --- sections that no longer exist
  '/repositories/': '/projects/',
  '/plugins/': '/',

  // Teaching folds into the CV rather than carrying a section for one course.
  '/teaching/': '/cv/',
  '/teaching/dati_e_algoritmi/': '/cv/',
  '/teachings/data-science-fundamentals/': '/cv/',
  '/teachings/introduction-to-machine-learning/': '/cv/',

  // --- al-folio demo content that was never real
  '/books/': '/',
  '/books/2024/': '/',
  '/books/the_godfather/': '/',
  '/books/category/classics/': '/',
  '/books/category/crime/': '/',
  '/books/category/historical-fiction/': '/',
  '/books/category/mystery/': '/',
  '/books/category/novels/': '/',
  '/books/category/thriller/': '/',
  '/books/tag/top-100/': '/',

  /*
   * Jekyll split `categories: Python, Programming, Scientific Computing` on
   * whitespace, so "Scientific Computing" became two bogus category archives.
   * The new site reads categories as a real list, so these have no successor.
   */
  '/blog/category/computing/': '/blog/',
  '/blog/category/scientific/': '/blog/',

  // Lowercase variants of the two case-sensitive legacy post slugs. Jekyll kept
  // filename case; anyone hand-typing or lowercasing the URL would 404 otherwise.
  '/blog/2021/dsp-il-suono-in-digitale/': '/blog/2021/DSP-il-suono-in-digitale/',
  '/blog/2022/principles-of-statistic/': '/blog/2022/Principles-of-statistic/',
};
