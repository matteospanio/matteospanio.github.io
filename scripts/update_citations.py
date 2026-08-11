#!/usr/bin/env python3
"""Refresh citation counts in src/data/citations.json.

Everything is keyed by BibTeX entry key — the only identifier this site controls.
Sources are matched onto bibliography entries by google_scholar_id or by a
normalised title; anything that matches no entry is dropped, because a count for
a paper the site does not list has nowhere to go.

Source priority, and why:

  Google Scholar is primary. It is the only source that currently has the whole
  record (31 citations across 13 papers as of the migration). OpenAlex, despite
  being the more principled API, has this author fragmented across five author
  records — the ORCID-linked one lists 9 works and 4 citations. Treating OpenAlex
  as primary silently deleted two thirds of the real numbers, so it is a
  supplement: it fills papers Scholar misses.

  Scholar is also the fragile one: it blocks datacenter IPs, so a run that fails
  must leave the existing data untouched rather than zeroing it. The merge takes
  the maximum across sources for exactly this reason.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "citations.json"
BIB = ROOT / "src" / "data" / "papers.bib"

ORCID = "0000-0002-2436-7208"
MAILTO = "spanio@dei.unipd.it"  # OpenAlex polite pool
SCHOLAR_USER = "CEWwcjUAAAAJ"


def title_key(title: str) -> str:
    """Letters and digits only: sources differ in case, punctuation, accents and
    stray LaTeX braces."""
    text = unicodedata.normalize("NFD", title.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", text)


def read_bibliography() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Returns (title_key -> bibkey, scholar_id -> bibkey, bibkey -> title)."""
    text = BIB.read_text(encoding="utf-8")
    by_title: dict[str, str] = {}
    by_scholar: dict[str, str] = {}
    titles: dict[str, str] = {}

    for entry in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", text, re.S):
        key, body = entry.group(1).strip(), entry.group(2)
        match = re.search(r"title\s*=\s*\{(.+?)\}\s*,?\s*\n", body, re.S)
        if match:
            title = re.sub(r"\s+", " ", match.group(1).replace("{", "").replace("}", "")).strip()
            titles[key] = title
            by_title[title_key(title)] = key
        scholar = re.search(r"google_scholar_id\s*=\s*\{([^}]+)\}", body)
        if scholar:
            by_scholar[scholar.group(1).strip()] = key

    return by_title, by_scholar, titles


def fetch_openalex() -> tuple[dict[str, dict], dict]:
    """{title_key: record} plus author-level summary stats. Never raises."""
    headers = {"User-Agent": f"matteospanio.github.io (mailto:{MAILTO})"}
    works: dict[str, dict] = {}
    summary: dict = {}

    try:
        with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
            author = client.get(f"https://api.openalex.org/authors/orcid:{ORCID}")
            if author.status_code == 200:
                stats = author.json().get("summary_stats", {})
                summary = {"hIndex": stats.get("h_index"), "i10Index": stats.get("i10_index")}

            cursor = "*"
            while cursor:
                response = client.get(
                    "https://api.openalex.org/works",
                    params={
                        "filter": f"author.orcid:{ORCID}",
                        "per-page": 200,
                        "cursor": cursor,
                        "select": "title,publication_year,cited_by_count,counts_by_year,doi",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                for work in payload.get("results", []):
                    title = work.get("title")
                    if not title:
                        continue
                    works[title_key(title)] = {
                        "title": title,
                        "year": str(work.get("publication_year") or ""),
                        "citations": int(work.get("cited_by_count") or 0),
                        "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
                        "countsByYear": {
                            str(c["year"]): c["cited_by_count"] for c in work.get("counts_by_year", [])
                        },
                    }
                cursor = payload.get("meta", {}).get("next_cursor")
    except Exception as error:  # noqa: BLE001 - a dead API must not fail the run
        print(f"OpenAlex unavailable: {error}", file=sys.stderr)
        return {}, {}

    return works, summary


def fetch_scholar() -> dict[str, dict]:
    """{scholar_pub_id or title_key: record}. Never raises."""
    try:
        from scholarly import scholarly
    except ImportError:
        print("scholarly not installed; skipping Google Scholar", file=sys.stderr)
        return {}

    try:
        author = scholarly.fill(
            scholarly.search_author_id(SCHOLAR_USER), sections=["publications"]
        )
    except Exception as error:  # noqa: BLE001
        print(f"Google Scholar unavailable: {error}", file=sys.stderr)
        return {}

    out: dict[str, dict] = {}
    for pub in author.get("publications", []):
        bib = pub.get("bib", {})
        title = bib.get("title")
        if not title:
            continue
        record = {
            "title": title,
            "year": str(bib.get("pub_year") or ""),
            "citations": int(pub.get("num_citations") or 0),
        }
        # Key by the Scholar pub id when present so the bib's google_scholar_id
        # can match it directly, and by title as a fallback.
        pub_id = (pub.get("author_pub_id") or "").split(":")[-1]
        if pub_id:
            out[pub_id] = record
        out.setdefault(title_key(title), record)
    return out


def main() -> int:
    by_title, by_scholar, _ = read_bibliography()

    previous: dict = {}
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8")).get("papers", {})

    papers: dict[str, dict] = {key: dict(value) for key, value in previous.items()}

    def merge(source_key: str, record: dict, source_name: str) -> bool:
        """Attribute one source record to a bibliography entry. Returns True if matched."""
        bibkey = by_scholar.get(source_key) or by_title.get(title_key(record.get("title", "")))
        if not bibkey:
            return False

        existing = papers.get(bibkey, {})
        fetched = int(record.get("citations") or 0)
        held = int(existing.get("citations") or 0)

        merged = dict(existing)
        merged["title"] = existing.get("title") or record.get("title")
        merged["year"] = existing.get("year") or record.get("year")
        # Never let a throttled or incomplete source zero out a real measurement.
        merged["citations"] = max(fetched, held)
        if fetched >= held:
            merged["source"] = source_name
        if record.get("doi"):
            merged["doi"] = record["doi"]
        if record.get("countsByYear"):
            merged["countsByYear"] = record["countsByYear"]

        papers[bibkey] = merged
        return True

    scholar = fetch_scholar()
    openalex, summary = fetch_openalex()

    matched = {"scholar": 0, "openalex": 0}
    dropped: list[str] = []

    for key, record in scholar.items():
        if merge(key, record, "scholar"):
            matched["scholar"] += 1
    for key, record in openalex.items():
        if merge(key, record, "openalex"):
            matched["openalex"] += 1
        else:
            dropped.append(record.get("title", "")[:70])

    today = date.today().isoformat()
    payload = {
        "schemaVersion": 2,
        "generatedAt": today,
        "sources": {
            "scholar": {"fetchedAt": today if scholar else None, "ok": bool(scholar),
                        "matched": matched["scholar"]},
            "openalex": {"fetchedAt": today if openalex else None, "ok": bool(openalex),
                         "matched": matched["openalex"]},
        },
        "summary": summary,
        "papers": dict(sorted(papers.items())),
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total = sum(int(p.get("citations") or 0) for p in papers.values())
    print(f"wrote {OUT.relative_to(ROOT)}: {len(papers)} papers, {total} citations")
    print(f"  matched — scholar: {matched['scholar']}, openalex: {matched['openalex']}")
    if dropped:
        print(f"  not in bibliography (ignored): {len(dropped)}")
        for title in dropped:
            print(f"    · {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
