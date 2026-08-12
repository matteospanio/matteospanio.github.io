#!/usr/bin/env python3
"""Build src/data/viz/map-variants.json — the same embedding under other knobs.

The map's caveat says "read the geometry loosely" because a UMAP picture of a
corpus this small is partly a property of `random_state` and `n_neighbors`.
This script turns that sentence into something a visitor can *do*: it refits
the projection under a grid of seeds and neighbourhood sizes and ships all of
the layouts, so the site can tween between them. The picture changes, the
neighbourhoods mostly don't — which is exactly the honest reading.

Two decisions keep the comparison fair:

1. Every variant is Procrustes-aligned (rotation, reflection, scale) onto the
   canonical layout before shipping. UMAP's output frame is arbitrary, so
   without alignment most of the visible motion would be a meaningless global
   rotation and the scrubber would overstate the instability.

2. Variant 0 IS the canonical layout, copied verbatim from embedding-map.json
   rather than recomputed, so the scrubber's resting state is bit-identical to
   the shipped map and CI can hold both files to the same sourceHash.

Run after build_embedding_map.py, with the same venv.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_embedding_map import (  # noqa: E402
    MODEL_NAME,
    collect_items,
    principal_frame,
    source_hash,
)

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "src" / "data" / "viz" / "embedding-map.json"
OUT = ROOT / "src" / "data" / "viz" / "map-variants.json"

# The canonical run is (seed 42, k 10). The grid varies one knob at a time and
# then both, which is enough spread to show the envelope without shipping a
# hundred layouts nobody will scrub through.
CANONICAL = (42, 10)
COMBOS: list[tuple[int, int]] = [
    (42, 10),
    (42, 5),
    (42, 15),
    (7, 5),
    (7, 10),
    (7, 15),
    (1234, 5),
    (1234, 10),
    (1234, 15),
    (2024, 5),
    (2024, 10),
    (2024, 15),
]


def align_to(coords, reference):
    """Best rotation+reflection+scale of `coords` onto `reference` (Procrustes)."""
    import numpy as np
    from scipy.linalg import orthogonal_procrustes

    a = coords - coords.mean(axis=0)
    b = reference - reference.mean(axis=0)
    rotation, scale_num = orthogonal_procrustes(a, b)
    scale = scale_num / float((a**2).sum())
    return a @ rotation * scale + reference.mean(axis=0)


def main() -> int:
    if not CANON.exists():
        print(f"{CANON} missing — run build_embedding_map.py first", file=sys.stderr)
        return 1
    canonical = json.loads(CANON.read_text(encoding="utf-8"))

    items, _status = collect_items()
    if source_hash(items) != canonical["sourceHash"]:
        print(
            "corpus changed since embedding-map.json was built — "
            "run build_embedding_map.py first",
            file=sys.stderr,
        )
        return 1

    import numpy as np
    import torch
    import umap
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics import silhouette_score

    order = [node["id"] for node in canonical["nodes"]]
    by_id = {item["id"]: item for item in items}
    items = [by_id[i] for i in order]
    labels = [item["theme"] for item in items]
    reference = np.array([[node["x"], node["y"]] for node in canonical["nodes"]])

    torch.manual_seed(42)
    np.random.seed(42)
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    model.eval()

    documents = [f"passage: {doc}" for item in items for doc in item["docs"]]
    owners = np.asarray(
        [index for index, item in enumerate(items) for _ in item["docs"]]
    )
    with torch.no_grad():
        chunk_vectors = model.encode(
            documents,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    variants = []
    for seed, k in COMBOS:
        if (seed, k) == CANONICAL:
            coords = reference
            silhouette = canonical["sanity"]["silhouetteVsThemes"]
        else:
            projected = umap.UMAP(
                n_neighbors=min(k, len(documents) - 1),
                min_dist=0.30,
                metric="cosine",
                n_components=2,
                random_state=seed,
                init="pca",
            ).fit_transform(chunk_vectors)
            folded = np.vstack(
                [projected[owners == index].mean(axis=0) for index in range(len(items))]
            )
            coords = align_to(principal_frame(folded), reference)
            silhouette = round(float(silhouette_score(coords, labels)), 4)

        variants.append(
            {
                "seed": seed,
                "k": k,
                "canonical": (seed, k) == CANONICAL,
                "silhouette": silhouette,
                "xy": [[round(float(x), 4), round(float(y), 4)] for x, y in coords],
            }
        )
        print(f"  seed {seed:>4} · k {k:>2} · silhouette {silhouette}")

    OUT.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "generatedAt": date.today().isoformat(),
                "sourceHash": canonical["sourceHash"],
                "note": (
                    "Each variant is the same chunk embedding refitted by UMAP "
                    "under a different seed and n_neighbors, Procrustes-aligned "
                    "to the canonical layout. Node order matches ids."
                ),
                "ids": order,
                "variants": variants,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)}: {len(variants)} projections of {len(order)} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
