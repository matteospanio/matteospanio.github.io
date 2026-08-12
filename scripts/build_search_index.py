#!/usr/bin/env python3
"""Build public/search-index.json — document vectors for in-browser search.

The site runs semantic search entirely client-side: transformers.js embeds the
visitor's query with Xenova/all-MiniLM-L6-v2 (the ONNX export of the model
used here), and ranks against these precomputed document vectors by cosine.
Nothing typed into the box leaves the page.

Why MiniLM and not the e5 family that draws the map: every multilingual
encoder carries a ~250k-token vocabulary, which puts the quantized download
above 100 MB. MiniLM's q8 ONNX is ~23 MB — the difference between a demo a
visitor will actually try and one they will not. The cost is that the few
Italian-language items are represented mostly by their English metadata; the
UI says so.

Vectors are stored int8 with a per-vector scale and base64-packed: 42 × 384
bytes ≈ 16 kB on the wire instead of ~100 kB of JSON floats. Cosine survives
the quantisation easily at ranking precision.

Run after build_embedding_map.py, with the same venv.
"""

from __future__ import annotations

import base64
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_embedding_map import collect_items, source_hash  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "src" / "data" / "viz" / "embedding-map.json"
OUT = ROOT / "public" / "search-index.json"

# Must stay in lockstep with the client model in EmbeddingMap.astro:
# sentence-transformers/all-MiniLM-L6-v2 is what Xenova/all-MiniLM-L6-v2 wraps.
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CLIENT_MODEL = "Xenova/all-MiniLM-L6-v2"


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
    from sentence_transformers import SentenceTransformer

    # Ship in the map's node order so the client can index straight into it.
    order = [node["id"] for node in canonical["nodes"]]
    by_id = {item["id"]: item for item in items}
    items = [by_id[i] for i in order]

    model = SentenceTransformer(MODEL, device="cpu")
    model.eval()

    documents = [doc for item in items for doc in item["docs"]]
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

    vectors = np.vstack(
        [chunk_vectors[owners == index].mean(axis=0) for index in range(len(items))]
    )
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    # int8 with per-vector scale: q = round(v / maxabs * 127).
    scales = np.abs(vectors).max(axis=1)
    quantized = np.round(vectors / scales[:, None] * 127).astype(np.int8)

    # Report the quantisation cost instead of assuming it away.
    restored = quantized.astype(np.float32) * (scales[:, None] / 127)
    drift = float(
        np.abs((vectors @ vectors.T) - (restored @ restored.T)).max()
    )

    OUT.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "generatedAt": date.today().isoformat(),
                "sourceHash": canonical["sourceHash"],
                "model": CLIENT_MODEL,
                "dims": int(vectors.shape[1]),
                "ids": order,
                "scales": [round(float(s), 6) for s in scales],
                "vectors": base64.b64encode(quantized.tobytes()).decode("ascii"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {OUT.relative_to(ROOT)}: {len(order)} vectors × {vectors.shape[1]} dims, "
        f"max cosine drift from int8: {drift:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
