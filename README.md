# matteospanio.github.io

Personal research site of Matteo Spanio — AI research engineer working on audio, music and
multimodal generative models. Built with [Astro](https://astro.build), deployed to GitHub Pages.

## Running it

```bash
npm ci
npm run dev          # http://localhost:4321
npm run build        # -> dist/
npm run preview
npm run check        # astro check (types + templates)
```

Node 22.12 or newer (see `.nvmrc`).

## How the content is organised

| Where | What |
|---|---|
| `src/content/blog/<slug>/index.mdx` | Blog posts, with images colocated in the same folder |
| `src/content/projects/<slug>/index.mdx` | Project cards |
| `src/content/news/*.md` | Short updates shown on the news timeline |
| `src/content/about.mdx` | The about copy on the homepage |
| `src/data/papers.bib` | The bibliography — the publications page is generated from it directly |
| `src/data/resume.json` | The single source for the CV page (JSON Resume format) |
| `src/config/site.ts` | Name, tagline, affiliation, navigation |

Editing `papers.bib` hot-reloads `/publications/` in dev: it is loaded as a real content
collection, not read at runtime.

### Adding a post

Create `src/content/blog/<slug>/index.mdx`. The `slug` field in the frontmatter is the URL segment
and **is case-sensitive** — GitHub Pages serves case-sensitively, and two existing posts rely on it.

Set `math: true` only if the post uses `$…$` or `$$…$$`; that gates the KaTeX stylesheet and its
webfonts onto the pages that need them.

Callouts are container directives:

```md
:::note{title="worth knowing"}
Body text.
:::
```

## Generated data

Every dataset is precomputed and committed, never fetched at page load:

| File | Built by | Refreshed |
|---|---|---|
| `src/data/citations.json` | `scripts/update_citations.py` | Mon/Wed/Fri via `update-citations.yml` |
| `src/data/viz/embedding-map.json` | `scripts/build_embedding_map.py` | **Manually** — `gh workflow run update-embeddings.yml` |
| `src/data/viz/wordcloud.json` | `scripts/build_wordcloud.py` | **Manually**, from local paper sources |

The embedding map is manual because it downloads a ~1 GB model. CI fails the build when the
corpus changes without it being rebuilt, so you get told rather than silently shipping a map with
a missing paper.

The word cloud is manual because it reads the LaTeX sources of the published papers, which live
outside the repository:

```bash
python scripts/build_wordcloud.py [~/Scrivania/papers]
```

It takes every `.zip` in that directory except the ones named in `EXCLUDE` — unpublished work has
to be listed there or it ends up in a public figure. It ships two packs, one for desktop and a
shorter one for phones, because a wide cloud scaled to 390px renders its smallest terms at about
four pixels.

Citation counts come from Google Scholar first, with OpenAlex as a supplement. Scholar blocks
datacentre addresses and fails often, so the merge takes the maximum per paper: a failed fetch can
never zero out a real number. A paper with no measurement renders as an em dash, not as zero.

## Checks

```bash
node scripts/check_legacy_urls.mjs dist        # every URL the old Jekyll site served still resolves
node scripts/check_endpoints.mjs dist          # llms.txt, profile.json and the API endpoints are populated
node scripts/check_embedding_freshness.mjs     # the embedding map matches the current corpus
```

All three run in CI on every pull request. `scripts/legacy_urls.txt` lists the 60 paths inherited
from the al-folio site — **do not delete entries from it**; those URLs are already out in the world.
Add a page or a redirect in `src/config/redirects.ts` instead.

## Citable posts

Every post shows a BibTeX and APA citation block. A DOI is optional and hand-picked, one or two a
year — mint it by depositing the post's PDF on Zenodo and putting the resulting DOIs in the post's
frontmatter under `citation:`. Only then do the Google Scholar meta tags appear.

Generate a post PDF with:

```bash
npm run build && npx astro preview --port 4321 &
node scripts/build_post_pdf.mjs <slug> <year> [version]
```

## Deployment

Push to `master`. `deploy.yml` builds and publishes via `actions/deploy-pages`.

The repository's Pages source must be set to **GitHub Actions** (Settings → Pages → Build and
deployment → Source). With the legacy branch source it will build and then refuse to deploy.

## Contact form

`src/components/ContactForm.astro` posts to [Web3Forms](https://web3forms.com). The access key is
designed to be public and is bound to the destination inbox, so it is not a secret — but it does
have to be present at build time in **two** places, because `.env` is git-ignored:

- locally, `PUBLIC_WEB3FORMS_KEY` (or `WEB3FORMS_PUBLIC_KEY`) in `.env`
- in CI, the repository **variable** `PUBLIC_WEB3FORMS_KEY`, passed to the build in `deploy.yml`

Set the second with `gh variable set PUBLIC_WEB3FORMS_KEY --body <key>`. Without it the deployed
form ships disabled with a notice pointing at the email address, even though it works locally. The
form works without JavaScript.
