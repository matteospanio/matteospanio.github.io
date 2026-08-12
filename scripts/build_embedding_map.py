#!/usr/bin/env python3
"""Build src/data/viz/embedding-map.json — the 2-D map of the research corpus.

The honest problem this script works around
-------------------------------------------
The corpus is 17 papers, 5 posts, 6 projects and 8 news items: 36 items, of which
only 8 papers carry an abstract. UMAP on n=36 does not find structure, it invents
an arrangement that *looks* like structure and changes with the seed. Two things
keep the output defensible:

1. Raise the point count by chunking. Every source item contributes a base
   document (title + description-ish text) and, when it has a body or an abstract
   long enough to justify it, extra chunks of roughly 120-250 words. That lifts
   the projection from ~36 points to ~90, which is still small but no longer
   degenerate. Each chunk records its parent id, so chunk coordinates are averaged
   back into exactly one node per source item for display.

2. Colour never comes from clustering. Every item is labelled with one of six
   declared themes — taken from the content frontmatter where it exists, and from
   the explicit table below for bibliography entries and news. Positions come from
   the embedding; colours come from the labels. No KMeans, no HDBSCAN: inventing
   clusters at this n and then colouring by them would be circular.

The model is intfloat/multilingual-e5-base. Multilingual is load-bearing: one post
and two theses are in Italian, and a monolingual encoder pushes them into a corner
of their own that reads as a topic but is only a language.

The "sanity" block exists so the map's meaningfulness stays visible rather than
assumed. silhouetteVsThemes near 0 means the 2-D picture does not separate the
declared themes and should not be sold as if it did.

Never fabricates coordinates: if the model cannot be loaded, the script writes a
JSON with sources.model.ok = false and an empty nodes array.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Iterable

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "viz" / "embedding-map.json"
BIB = ROOT / "src" / "data" / "papers.bib"
CONTENT = ROOT / "src" / "content"

MODEL_NAME = "intfloat/multilingual-e5-base"
SEED = 42
K_NEIGHBOURS = 3
EDGE_MIN_WEIGHT = 0.72

THEMES: list[dict[str, str]] = [
    {
        "id": "cultural-heritage",
        "label": "AI for audio cultural heritage",
        "color": "#5eead4",
    },
    {"id": "multimodal", "label": "Multimodal and crossmodal AI", "color": "#c084fc"},
    {
        "id": "symbolic-music",
        "label": "Symbolic music and LilyPond",
        "color": "#fbbf24",
    },
    {"id": "dsp-tooling", "label": "Audio DSP tooling", "color": "#4ade80"},
    {"id": "musicology", "label": "Musicology and performance", "color": "#f87171"},
    {
        "id": "engineering",
        "label": "Software and research engineering",
        "color": "#7dd3fc",
    },
]
THEME_IDS = {t["id"] for t in THEMES}

# Bibliography entries carry no theme field, so the mapping is declared here and
# nowhere else. Tape / ARP / computer-vision-on-tapes work is cultural heritage;
# taste-and-sound and emotion work is multimodal; LilyPond work is symbolic music;
# TorchFX is DSP tooling; the two clarinet theses and the Spohr reduction are
# musicology; the repository-template paper is research engineering.
PAPER_THEMES: dict[str, str] = {
    "10.1007/978-3-031-51026-7_26": "cultural-heritage",
    "https://doi.org/10.13140/rg.2.2.36838.50247": "cultural-heritage",
    "https://doi.org/10.13140/rg.2.2.17327.82088": "musicology",
    "sphor:woo15": "musicology",
    "https://doi.org/10.13140/rg.2.2.24143.56489": "musicology",
    "bosi2024a": "cultural-heritage",
    "ieeeaccess2024": "cultural-heritage",
    "Cinar2024": "cultural-heritage",
    "Spanio2024": "multimodal",
    "spanio_frontiers_2025": "multimodal",
    "fiordelmondo_nime_2025": "engineering",
    "spanio2025torchfx": "dsp-tooling",
    "spanio2026bmdataset": "symbolic-music",
    "spanio2026multimodal": "multimodal",
    "canazza2026preserving": "cultural-heritage",
    "spanio2026lilypond": "symbolic-music",
    "pretto2026advanced": "cultural-heritage",
    "spanio2026cbmi": "multimodal",
    "poltronieri2026notation": "symbolic-music",
    "spanio2026quantizednativeruntimeondevice": "engineering",
    "spanio2026fluxion": "engineering",
    "spanio2026review": "multimodal",
    "spanio2026": "multimodal",
}

# News items inherit the theme of what they announce. Two of them announce one
# paper from each of two themes (aixia2024, 2026-ItalIA); the tie is broken toward
# the paper named first in the item's own text, and the ambiguity is real — those
# two are the labels most likely to cost silhouette rather than earn it.
NEWS_THEMES: dict[str, str] = {
    "2026-ItalIA": "cultural-heritage",
    # TREC 2026: uncertainty-aware ASR/NLP for language-disorder screening —
    # speech into language, so multimodal is the closest declared area, though
    # it is the first item here that is clinical rather than musical.
    "2026-Trec": "multimodal",
    "aes2024NY": "cultural-heritage",
    "aixia2024": "multimodal",
    "ann_4": "engineering",
    "announcement_2": "cultural-heritage",
    "dafx2025": "dsp-tooling",
    "hf2025": "multimodal",
    "hf2026-lilybert": "symbolic-music",
}


# --------------------------------------------------------------------------- #
# text handling
# --------------------------------------------------------------------------- #


def squeeze(text: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def strip_latex(text: str) -> str:
    """BibTeX braces are a case-folding instruction, not content."""
    text = re.sub(r"\\['\"^`~=.]\{?(\w)\}?", r"\1", text)
    text = text.replace("{", "").replace("}", "").replace("\\&", "&")
    return squeeze(text)


def strip_markdown(text: str) -> str:
    """Cleaned prose from MDX: no frontmatter, code, JSX, directives or math.

    Code blocks are removed rather than kept because a fenced Python listing
    embeds to "this is Python", which every engineering item already says in
    prose, and it drowns the sentence that actually carries the topic.
    """
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"^(import|export)\s.+$", " ", text, flags=re.M)
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    text = re.sub(r"\$[^$\n]*\$", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> label
    text = re.sub(r"\[\^[^\]]*\]:?", " ", text)  # footnotes
    text = re.sub(r"^:::.*$", " ", text, flags=re.M)  # ::: directives
    text = re.sub(r"<[^>\n]{1,200}>", " ", text)  # JSX / HTML tags
    text = re.sub(r"[`*_>|]", " ", text)
    return squeeze(text)


def words(text: str) -> list[str]:
    return text.split()


def split_words(text: str, size: int) -> list[str]:
    """Even-ish pieces of at most ~`size` words.

    Ceiling, not rounding: a 170-word abstract at size 120 must become two pieces,
    because rounding it back to one is the same as not chunking at all, and
    chunking is the only thing standing between this corpus and a projection of 35
    points.
    """
    tokens = words(text)
    if len(tokens) <= size:
        return [text] if tokens else []
    count = -(-len(tokens) // size)
    step = -(-len(tokens) // count)
    pieces = [" ".join(tokens[i : i + step]) for i in range(0, len(tokens), step)]
    if len(pieces) > 1 and len(words(pieces[-1])) < size // 3:
        pieces[-2] = pieces[-2] + " " + pieces.pop()
    return pieces


def chunk_prose(body: str, target: int, max_chunks: int) -> list[str]:
    """Body prose to at most `max_chunks` pieces of roughly `target` words.

    Headings are the preferred cut, but they cannot be relied on: the project
    write-ups have none at all, and splitting on them alone left each project as a
    single 500-word chunk that the encoder then truncated at 512 tokens. So any
    section still well over target is cut again by word count.

    Merging (never dropping) keeps every word of the body in exactly one chunk, so
    a long post cannot end up silently represented by its introduction.
    """
    sections = [p.strip() for p in re.split(r"^##+\s", body, flags=re.M) if p.strip()]
    if not sections:
        sections = [body.strip()] if body.strip() else []

    parts: list[str] = []
    for section in sections:
        parts.extend(
            split_words(section, target)
            if len(words(section)) > target * 1.6
            else [section]
        )

    # A part shorter than 40 words is a caption, not a topic: fold it forward.
    merged: list[str] = []
    for part in parts:
        if merged and len(words(part)) < 40:
            merged[-1] += " " + part
        else:
            merged.append(part)

    while len(merged) > max_chunks:
        sizes = [len(words(m)) for m in merged]
        i = min(range(len(merged) - 1), key=lambda j: sizes[j] + sizes[j + 1])
        merged[i : i + 2] = [merged[i] + " " + merged[i + 1]]
    return merged


def short_title(title: str, limit: int = 38) -> str:
    head = re.split(r"\s[-–—]\s|:\s|\?\s", title, maxsplit=1)[0].strip(" .?:–—-")
    if len(head) > limit:
        head = head[: limit - 1].rsplit(" ", 1)[0] + "…"
    return head or title[:limit]


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #


def parse_bib(text: str) -> list[dict[str, str]]:
    """Brace-aware BibTeX reader. Abstracts contain braces, so regex-per-field
    without balancing truncates them."""
    entries: list[dict[str, str]] = []
    for match in re.finditer(r"@(\w+)\s*\{", text):
        start = match.end() - 1
        depth, i = 0, start
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = text[start + 1 : i]
        key, _, rest = body.partition(",")
        fields: dict[str, str] = {
            "__type__": match.group(1).lower(),
            "__key__": key.strip(),
        }

        pos = 0
        while True:
            field = re.compile(r"(\w+)\s*=\s*").search(rest, pos)
            if not field:
                break
            j = field.end()
            if j < len(rest) and rest[j] == "{":
                depth, k = 0, j
                while k < len(rest):
                    if rest[k] == "{":
                        depth += 1
                    elif rest[k] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                value, pos = rest[j + 1 : k], k + 1
            elif j < len(rest) and rest[j] == '"':
                k = rest.find('"', j + 1)
                value, pos = rest[j + 1 : k], k + 1
            else:
                k = rest.find(",", j)
                k = len(rest) if k == -1 else k
                value, pos = rest[j:k], k
            fields[field.group(1).lower()] = strip_latex(value)
        entries.append(fields)
    return entries


def read_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    import yaml

    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)) or {}, match.group(2)


def year_of(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if hasattr(value, "year"):
        return int(value.year)
    digits = re.search(r"\d{4}", str(value or ""))
    return int(digits.group(0)) if digits else None


def collect_items() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One record per source item, each with its list of documents to embed."""
    items: list[dict[str, Any]] = []
    status: dict[str, Any] = {}

    # -- publications ------------------------------------------------------- #
    try:
        entries = parse_bib(BIB.read_text(encoding="utf-8"))
        for entry in entries:
            key = entry["__key__"]
            theme = PAPER_THEMES.get(key)
            if theme is None:
                print(
                    f"  ! no declared theme for bib key {key}; skipped", file=sys.stderr
                )
                continue
            title = entry.get("title", "")
            venue = (
                entry.get("journal")
                or entry.get("booktitle")
                or entry.get("howpublished")
                or entry.get("type")
                or entry.get("publisher")
            )
            abstract = entry.get("abstract", "")
            # `note` carries the topical sentence for entries that have no
            # abstract — without it the Spohr reduction is four words long and
            # falls under the minimum, disappearing from the map entirely.
            base = " ".join(
                x
                for x in (
                    title,
                    venue or "",
                    entry.get("abbr", ""),
                    entry.get("note", ""),
                    abstract,
                )
                if x
            )
            docs = [base]
            if len(words(abstract)) >= 140:
                docs += chunk_prose(abstract, 120, 3)
            items.append(
                {
                    "id": key,
                    "kind": "paper",
                    "theme": theme,
                    "title": title,
                    "short": short_title(title),
                    "year": year_of(entry.get("year")),
                    "venue": entry.get("abbr") or venue,
                    "url": f"/publications/#{key}",
                    "docs": docs,
                }
            )
        status["bib"] = {"ok": True, "entries": len(entries), "used": len(items)}
    except Exception as error:  # noqa: BLE001
        print(f"papers.bib unreadable: {error}", file=sys.stderr)
        status["bib"] = {"ok": False, "reason": str(error)}

    # -- blog posts --------------------------------------------------------- #
    posts = 0
    try:
        for path in sorted((CONTENT / "blog").glob("*/index.md*")):
            data, body = read_frontmatter(path.read_text(encoding="utf-8"))
            if data.get("draft"):
                continue
            theme = data.get("theme")
            if theme not in THEME_IDS:
                print(
                    f"  ! post {path.parent.name} has no declared theme; skipped",
                    file=sys.stderr,
                )
                continue
            prose = strip_markdown(body)
            budget = min(6, max(2, round(len(words(prose)) / 150)))
            title = str(data.get("title", path.parent.name))
            year = year_of(data.get("date"))
            items.append(
                {
                    "id": f"post:{data.get('slug', path.parent.name)}",
                    "kind": "post",
                    "theme": theme,
                    "title": title,
                    "short": short_title(title),
                    "year": year,
                    "venue": None,
                    "url": f"/blog/{year}/{data.get('slug', path.parent.name)}/",
                    "docs": [f"{title}. {data.get('description', '')}"]
                    + chunk_prose(prose, 200, budget),
                }
            )
            posts += 1
        status["blog"] = {"ok": True, "used": posts}
    except Exception as error:  # noqa: BLE001
        print(f"blog unreadable: {error}", file=sys.stderr)
        status["blog"] = {"ok": False, "reason": str(error)}

    # -- projects ----------------------------------------------------------- #
    projects = 0
    try:
        for path in sorted((CONTENT / "projects").glob("*/index.md*")):
            data, body = read_frontmatter(path.read_text(encoding="utf-8"))
            if data.get("draft"):
                continue
            theme = data.get("theme")
            if theme not in THEME_IDS:
                print(
                    f"  ! project {path.parent.name} has no declared theme; skipped",
                    file=sys.stderr,
                )
                continue
            prose = strip_markdown(body)
            budget = min(6, max(2, round(len(words(prose)) / 150)))
            title = str(data.get("title", path.parent.name))
            items.append(
                {
                    "id": f"project:{path.parent.name}",
                    "kind": "project",
                    "theme": theme,
                    "title": title,
                    "short": short_title(title),
                    "year": year_of(data.get("year")),
                    "venue": None,
                    "url": f"/projects/{path.parent.name}/",
                    "docs": [
                        f"{title}. {data.get('tagline', '')}. {data.get('description', '')}"
                    ]
                    + chunk_prose(prose, 150, budget),
                }
            )
            projects += 1
        status["projects"] = {"ok": True, "used": projects}
    except Exception as error:  # noqa: BLE001
        print(f"projects unreadable: {error}", file=sys.stderr)
        status["projects"] = {"ok": False, "reason": str(error)}

    # -- news --------------------------------------------------------------- #
    news = 0
    try:
        for path in sorted((CONTENT / "news").glob("*.md")):
            data, body = read_frontmatter(path.read_text(encoding="utf-8"))
            slug = path.stem
            theme = NEWS_THEMES.get(slug)
            if theme is None:
                print(
                    f"  ! no declared theme for news {slug}; skipped", file=sys.stderr
                )
                continue
            title = str(data.get("title", slug))
            items.append(
                {
                    "id": f"news:{slug}",
                    "kind": "news",
                    "theme": theme,
                    "title": title,
                    "short": short_title(title),
                    "year": year_of(data.get("date")),
                    "venue": None,
                    "url": f"/news/#{slug}",
                    "docs": [f"{title}. {strip_markdown(body)}"],
                }
            )
            news += 1
        status["news"] = {"ok": True, "used": news}
    except Exception as error:  # noqa: BLE001
        print(f"news unreadable: {error}", file=sys.stderr)
        status["news"] = {"ok": False, "reason": str(error)}

    # Six words is enough to place a point; anything below that is a stub whose
    # position would be noise. Dropping is reported rather than silent — an item
    # missing from the map without explanation is the failure mode to avoid.
    for item in items:
        item["docs"] = [squeeze(d) for d in item["docs"] if len(words(squeeze(d))) >= 6]
    kept = [i for i in items if i["docs"]]
    dropped = [i["id"] for i in items if not i["docs"]]
    if dropped:
        print(f"  ! too little text to place: {', '.join(dropped)}", file=sys.stderr)
        status["dropped"] = dropped
    return kept, status


def source_hash(items: Iterable[dict[str, Any]]) -> str:
    """Stable over content identity, not content text: CI compares this to spot a
    map built before an item was added or removed."""
    ids = sorted(unicodedata.normalize("NFC", i["id"]) for i in items)
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #


def principal_frame(coords):
    """Rotate onto principal axes with a fixed sign convention.

    PCA alone does not pin the map down: eigenvector signs are arbitrary, so two
    identical runs can come out mirrored. Forcing each axis to positive skew (with
    the extreme point as a tie-break) removes that last degree of freedom.
    """
    import numpy as np
    from sklearn.decomposition import PCA

    rotated = PCA(n_components=2, random_state=SEED).fit_transform(coords)
    for axis in range(2):
        column = rotated[:, axis]
        skew = float(np.sum(column**3))
        sign = skew if abs(skew) > 1e-9 else float(column[np.argmax(np.abs(column))])
        if sign < 0:
            rotated[:, axis] *= -1
    rotated -= rotated.mean(axis=0)
    scale = float(np.max(np.abs(rotated)))
    return rotated / scale if scale > 0 else rotated


def seed_stability(
    chunk_vectors, owners_array, n_items: int, n_neighbors: int, coords
) -> float | None:
    """How much of the layout survives changing the random seed.

    This is the number that decides whether the map may be shown at all. At n=36
    a UMAP picture can be pure seed artefact, and nothing else in the sanity block
    would reveal it: silhouette, intra and inter similarity are all computed
    against the same single run. So the projection is refitted under three other
    seeds and the pairwise node-distance matrices are compared by Spearman
    correlation. Near 1.0 means the arrangement is a property of the corpus; near
    0 means it is a property of `random_state` and the map is decoration.
    """
    import numpy as np
    import umap
    from scipy.spatial.distance import pdist
    from scipy.stats import spearmanr

    reference = pdist(coords)
    scores: list[float] = []
    for seed in (7, 1234, 2024):
        try:
            other = umap.UMAP(
                n_neighbors=n_neighbors,
                min_dist=0.30,
                metric="cosine",
                n_components=2,
                random_state=seed,
                init="pca",
            ).fit_transform(chunk_vectors)
        except Exception as error:  # noqa: BLE001
            print(
                f"  ! stability check at seed {seed} failed: {error}", file=sys.stderr
            )
            continue
        folded = np.vstack(
            [other[owners_array == index].mean(axis=0) for index in range(n_items)]
        )
        scores.append(
            float(spearmanr(reference, pdist(principal_frame(folded))).correlation)
        )
    return round(sum(scores) / len(scores), 4) if scores else None


def build_edges(embeddings, ids: list[str]):
    """Cosine kNN, k=3, undirected and deduplicated."""
    import numpy as np

    similarity = embeddings @ embeddings.T
    np.fill_diagonal(similarity, -1.0)
    seen: dict[tuple[str, str], float] = {}
    rejected = 0
    for i in range(len(ids)):
        for j in np.argsort(-similarity[i])[:K_NEIGHBOURS]:
            weight = float(similarity[i, j])
            if weight < EDGE_MIN_WEIGHT:
                rejected += 1
                continue
            pair = (
                (ids[i], ids[int(j)]) if ids[i] < ids[int(j)] else (ids[int(j)], ids[i])
            )
            seen[pair] = max(seen.get(pair, 0.0), weight)
    edges = [
        {"s": s, "t": t, "w": round(w, 4)}
        for (s, t), w in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    return edges, rejected


def write(payload: dict[str, Any]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    today = date.today().isoformat()
    items, status = collect_items()
    chunk_total = sum(len(i["docs"]) for i in items)

    skeleton: dict[str, Any] = {
        "schemaVersion": 1,
        "generatedAt": today,
        "model": MODEL_NAME,
        "projection": {
            "method": "umap",
            "seed": SEED,
            "n_neighbors": min(10, max(2, chunk_total - 1)),
            "min_dist": 0.3,
            "metric": "cosine",
            "note": (
                "UMAP is fitted on chunk documents, chunk coordinates are averaged "
                "into one node per source item, then rotated onto principal axes "
                "and scaled uniformly (aspect preserved) into [-1, 1]."
            ),
        },
        "sourceHash": source_hash(items),
    }

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
        import torch
        import umap
        from sklearn.metrics import silhouette_score

        torch.manual_seed(SEED)
        np.random.seed(SEED)
        # CPU on purpose. The corpus is ~90 short documents, so the GPU buys
        # seconds at most, and it costs reproducibility: cuDNN kernels are not
        # bit-identical to the CPU ones, so the same corpus would land in slightly
        # different places depending on which machine ran the build.
        model = SentenceTransformer(MODEL_NAME, device="cpu")
        model.eval()
    except Exception as error:  # noqa: BLE001 - a missing model must not fake a map
        reason = f"{type(error).__name__}: {error}"
        print(f"model unavailable: {reason}", file=sys.stderr)
        write(
            skeleton
            | {
                "sanity": {
                    "n": 0,
                    "chunks": 0,
                    "silhouetteVsThemes": None,
                    "meanIntraTheme": None,
                    "meanInterTheme": None,
                },
                "sources": status | {"model": {"ok": False, "reason": reason}},
                "themes": [],
                "nodes": [],
                "edges": [],
            }
        )
        print(
            f"wrote {OUT.relative_to(ROOT)}: 0 nodes (model unavailable — no coordinates faked)"
        )
        return 1

    documents = [f"passage: {doc}" for item in items for doc in item["docs"]]
    owners = [index for index, item in enumerate(items) for _ in item["docs"]]

    with torch.no_grad():
        chunk_vectors = model.encode(
            documents,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    owners_array = np.asarray(owners)
    item_vectors = np.vstack(
        [
            chunk_vectors[owners_array == index].mean(axis=0)
            for index in range(len(items))
        ]
    )
    item_vectors /= np.linalg.norm(item_vectors, axis=1, keepdims=True)

    n_neighbors = min(10, len(documents) - 1)
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        min_dist=0.30,
        metric="cosine",
        n_components=2,
        random_state=SEED,
        init="pca",
    )
    chunk_coords = reducer.fit_transform(chunk_vectors)
    item_coords = np.vstack(
        [
            chunk_coords[owners_array == index].mean(axis=0)
            for index in range(len(items))
        ]
    )
    item_coords = principal_frame(item_coords)

    labels = [item["theme"] for item in items]
    distinct = sorted(set(labels))
    silhouette_2d = silhouette_2d_high = None
    if len(distinct) > 1 and len(items) > len(distinct):
        silhouette_2d = round(float(silhouette_score(item_coords, labels)), 4)
        silhouette_2d_high = round(
            float(silhouette_score(item_vectors, labels, metric="cosine")), 4
        )

    similarity = item_vectors @ item_vectors.T
    codes = np.array([distinct.index(label) for label in labels])
    same = np.equal.outer(codes, codes)
    upper = np.triu(np.ones_like(similarity, dtype=bool), k=1)
    intra = similarity[same & upper]
    inter = similarity[~same & upper]

    stability = seed_stability(
        chunk_vectors, owners_array, len(items), n_neighbors, item_coords
    )
    edges, floor_rejected = build_edges(item_vectors, [item["id"] for item in items])

    # The map comes out markedly wider than it is tall, because this corpus is
    # essentially one topical gradient rather than a plane of clusters. The extent
    # is published so the canvas can size itself to the real shape; stretching the
    # short axis to fill a square would manufacture separation that is not there.
    extent = {
        "x": [
            round(float(item_coords[:, 0].min()), 4),
            round(float(item_coords[:, 0].max()), 4),
        ],
        "y": [
            round(float(item_coords[:, 1].min()), 4),
            round(float(item_coords[:, 1].max()), 4),
        ],
    }

    theme_counts = {theme: labels.count(theme) for theme in THEME_IDS}
    payload = skeleton | {
        "projection": skeleton["projection"]
        | {"n_neighbors": n_neighbors, "extent": extent},
        "sanity": {
            "n": len(items),
            "chunks": len(documents),
            "silhouetteVsThemes": silhouette_2d,
            "silhouetteVsThemesEmbedding": silhouette_2d_high,
            "meanIntraTheme": round(float(intra.mean()), 4) if intra.size else None,
            "meanInterTheme": round(float(inter.mean()), 4) if inter.size else None,
            "seedStability": stability,
            # e5 puts every pair of same-author documents above 0.8, so the 0.72
            # floor never actually bites here. Reported rather than quietly
            # retuned: an edge list is "the 3 nearest neighbours", not "everything
            # above a meaningful similarity".
            "edgeFloor": EDGE_MIN_WEIGHT,
            "edgeFloorRejected": floor_rejected,
            "edgeWeightRange": (
                [min(e["w"] for e in edges), max(e["w"] for e in edges)]
                if edges
                else None
            ),
            "crossThemeEdges": sum(
                1
                for e in edges
                if next(i for i in items if i["id"] == e["s"])["theme"]
                != next(i for i in items if i["id"] == e["t"])["theme"]
            ),
        },
        "sources": status | {"model": {"ok": True, "name": MODEL_NAME}},
        "themes": [t | {"n": theme_counts.get(t["id"], 0)} for t in THEMES],
        "nodes": [
            {
                "id": item["id"],
                "kind": item["kind"],
                "theme": item["theme"],
                "title": item["title"],
                "short": item["short"],
                "year": item["year"],
                "venue": item["venue"],
                "url": item["url"],
                "chunks": len(item["docs"]),
                "x": round(float(item_coords[index, 0]), 4),
                "y": round(float(item_coords[index, 1]), 4),
            }
            for index, item in enumerate(items)
        ],
        "edges": edges,
    }
    write(payload)

    sanity = payload["sanity"]
    print(
        f"wrote {OUT.relative_to(ROOT)}: {len(items)} nodes from {len(documents)} chunks, "
        f"{len(edges)} edges ({sanity['crossThemeEdges']} cross-theme), silhouette vs themes "
        f"{sanity['silhouetteVsThemes']} in 2-D / {sanity['silhouetteVsThemesEmbedding']} in 768-D, "
        f"intra {sanity['meanIntraTheme']} vs inter {sanity['meanInterTheme']}, "
        f"seed stability {sanity['seedStability']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
