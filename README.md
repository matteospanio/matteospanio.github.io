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

Three datasets are precomputed and committed, never fetched at page load:

| File | Built by | Refreshed |
|---|---|---|
| `src/data/citations.json` | `scripts/update_citations.py` | Mon/Wed/Fri via `update-citations.yml` |
| `src/data/viz/footprint.json` | `scripts/build_footprint.py` | Sundays via `update-footprint.yml` |
| `src/data/viz/timeline.json` | `scripts/build_timeline.py` | Sundays, same workflow |
| `src/data/viz/embedding-map.json` | `scripts/build_embedding_map.py` | **Manually** — `gh workflow run update-embeddings.yml` |

The embedding map is manual because it downloads a ~1 GB model. CI fails the build when the
corpus changes without it being rebuilt, so you get told rather than silently shipping a map with
a missing paper.

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

`src/components/ContactForm.astro` posts to [Web3Forms](https://web3forms.com). Set
`PUBLIC_WEB3FORMS_KEY` to an access key; the key is designed to be public and is bound to the
destination inbox. Until it is set, the form is disabled and the page points at the email address
instead. The form works without JavaScript.
