#!/usr/bin/env python3
"""Build src/data/viz/footprint.json — the numbers behind the footprint dashboard.

The dashboard is rendered as inline SVG at build time with no client-side
JavaScript, so this script does every bit of arithmetic and geometry that the
Astro component would otherwise have to do at runtime. In particular the
coauthor graph is *laid out here*: nodes carry final x/y in [-1, 1] and the
component only maps them onto a viewBox.

Four sources, in decreasing order of trustworthiness:

  citations   src/data/citations.json, written by update_citations.py. Local, so
              it never fails. Only some entries carry countsByYear (OpenAlex
              supplies it, Google Scholar does not), so the per-year series
              covers a strict subset of the total — reported as `yearlyCovered`
              rather than silently presented as the whole picture. The total is
              the sum of per-paper counts and is never derived from the series.
  github      via `gh api`, which is authenticated and has a sane rate limit.
              A curated repo list rather than "everything the account owns":
              the account is full of forks and coursework. Repos that 404 are
              skipped; `gh` follows transfer redirects, so results are
              deduplicated by full_name (music-flavor-analysis moved from the
              personal account to CSCPadova).
  huggingface public JSON API, no auth. `downloads` is HF's rolling 30-day
              figure; `downloadsAllTime` is the cumulative one. Both are kept
              because they answer different questions and conflating them
              would misstate reach by an order of magnitude.
  papers.bib  parsed here for the coauthor graph, because it is the only source
              that knows who was on which paper.

On failure a network source does not zero out: the previously written block is
carried over verbatim with its original fetchedAt, and `ok: false, stale: true`
is recorded in `sources`. Nothing is invented — a stale honest measurement is
labelled as such. With no previous file, the fields are null.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "src" / "data" / "papers.bib"
CITATIONS = ROOT / "src" / "data" / "citations.json"
COAUTHORS = ROOT / "src" / "data" / "coauthors.json"
OUT = ROOT / "src" / "data" / "viz" / "footprint.json"

ME = ("spanio", "matteo")

HF_AUTHOR = "csc-unipd"

# (owner, name) tried in order; the first that resolves wins. `gh` follows
# GitHub's redirect for transferred repos, so a personal-account miss can come
# back wearing the organisation's name.
# Extra repos outside the personal account that should still count.
EXTRA_REPOS = [
    ("CSCPadova", "lilybert"),
    ("CSCPadova", "lilybench"),
    ("CSCPadova", "dei-blade-template"),
    ("CSCPadova", "MTR-template"),
    ("CSCPadova", "reverse-detection"),
    ("CSCPadova", "music-flavor-analysis"),
]


# --------------------------------------------------------------------------
# text helpers
# --------------------------------------------------------------------------

ACCENTS = {
    "`": "\u0300", "'": "\u0301", '"': "\u0308", "^": "\u0302", "~": "\u0303",
    "=": "\u0304", ".": "\u0307", "c": "\u0327", "v": "\u030c", "u": "\u0306",
    "H": "\u030b", "r": "\u030a",
}

# Characters NFD will not decompose into "letter + mark".
TRANSLITERATE = str.maketrans({
    "ı": "i", "İ": "I", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L",
    "đ": "d", "Đ": "D", "ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
})


def _accent(match: re.Match) -> str:
    command, letter = match.group(1), match.group(2)
    return unicodedata.normalize("NFC", letter + ACCENTS[command])


def delatex(text: str) -> str:
    """Rod{\\`a} -> Rodà. Enough LaTeX to survive a bibliography, no more."""
    text = re.sub(r"\{\\([`'\"^~=.cvuHr])\s*\{?([A-Za-z])\}?\}", _accent, text)
    text = re.sub(r"\\([`'\"^~=.])\s*\{?([A-Za-z])\}?", _accent, text)
    text = re.sub(r"\\([cvuHr])\{([A-Za-z])\}", _accent, text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", text)).strip()


def fold(text: str) -> str:
    """Accent- and case-insensitive key for comparing names across sources."""
    text = text.translate(TRANSLITERATE)
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", text)


def slugify(text: str) -> str:
    text = text.translate(TRANSLITERATE)
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text)).strip("-")


# --------------------------------------------------------------------------
# bibliography
# --------------------------------------------------------------------------

def parse_bib(text: str) -> list[dict]:
    """Minimal BibTeX reader: entry key, plus brace-balanced field values.

    Written by hand because the only alternative is a dependency, and the bib
    file has hand-edited quirks (a missing comma in one author list) that a
    strict parser would reject outright.
    """
    entries: list[dict] = []
    index = 0
    while True:
        at = text.find("@", index)
        if at == -1:
            break
        brace = text.find("{", at)
        if brace == -1:
            break
        entry_type = text[at + 1:brace].strip().lower()

        depth, cursor = 1, brace + 1
        while cursor < len(text) and depth:
            depth += (text[cursor] == "{") - (text[cursor] == "}")
            cursor += 1
        body = text[brace + 1:cursor - 1]
        index = cursor

        key, _, rest = body.partition(",")
        fields: dict[str, str] = {}
        pos = 0
        while pos < len(rest):
            match = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*").match(rest, pos)
            if not match:
                break
            name, pos = match.group(1).lower(), match.end()
            if pos < len(rest) and rest[pos] == "{":
                depth, start = 1, pos + 1
                pos += 1
                while pos < len(rest) and depth:
                    depth += (rest[pos] == "{") - (rest[pos] == "}")
                    pos += 1
                value = rest[start:pos - 1]
            elif pos < len(rest) and rest[pos] == '"':
                start = pos + 1
                pos = rest.find('"', start) + 1
                value = rest[start:pos - 1]
            else:
                match_bare = re.compile(r"[^,]*").match(rest, pos)
                value, pos = match_bare.group(0), match_bare.end()
            fields[name] = value
            pos = rest.find(",", pos) + 1 or len(rest)

        entries.append({"key": key.strip(), "type": entry_type, "fields": fields})
    return entries


def split_authors(raw: str) -> list[str]:
    return [a for a in re.split(r"\s+and\s+", delatex(raw)) if a.strip()]


def parse_names(raw_names: list[list[str]]) -> list[list[tuple[str, str]]]:
    """Turn raw author strings into (last, first) pairs, per paper.

    "Rodà, Antonio" is unambiguous. "Antonio Rodà" is not, and one entry in the
    bib reads "Canazza Sergio" — a dropped comma that would otherwise invent a
    Mr. Sergio. So: surnames learned from the comma-separated forms win when a
    two-token name starts with one of them.
    """
    known: set[str] = set()
    for paper in raw_names:
        for name in paper:
            if "," in name:
                known.add(fold(name.split(",", 1)[0]))

    out: list[list[tuple[str, str]]] = []
    for paper in raw_names:
        people: list[tuple[str, str]] = []
        for name in paper:
            if "," in name:
                last, first = (part.strip() for part in name.split(",", 1))
            else:
                tokens = name.split()
                if len(tokens) == 1:
                    last, first = tokens[0], ""
                elif fold(tokens[0]) in known:
                    last, first = tokens[0], " ".join(tokens[1:])
                else:
                    last, first = tokens[-1], " ".join(tokens[:-1])
            people.append((last.strip(), first.strip()))
        out.append(people)
    return out


def load_coauthor_urls() -> dict[str, dict]:
    """{folded surname: {"urls": {folded firstname: url}, "any": url}}."""
    if not COAUTHORS.exists():
        return {}
    raw = json.loads(COAUTHORS.read_text(encoding="utf-8"))
    table: dict[str, dict] = {}
    for surname, records in raw.items():
        entry = table.setdefault(fold(surname), {"urls": {}, "any": None})
        for record in records:
            url = record.get("url")
            if not url:
                continue
            entry["any"] = entry["any"] or url
            for firstname in record.get("firstname", []):
                entry["urls"][fold(firstname)] = url
    return table


# Entry types that represent collaboration. `@misc` is excluded because the one
# @misc entry is a published score reduction whose "author" is Louis Spohr
# (1784-1859) — a composer credit, not a coauthor.
COLLABORATIVE_TYPES = {"article", "inproceedings", "conference", "incollection", "book"}


def build_coauthor_graph(entries: list[dict]) -> dict:
    raw_names, years = [], []
    for entry in entries:
        if entry.get("type", "").lower() not in COLLABORATIVE_TYPES:
            continue
        author = entry["fields"].get("author")
        if not author:
            continue
        raw_names.append(split_authors(author))
        year = re.search(r"\d{4}", entry["fields"].get("year", "") or "")
        years.append(int(year.group(0)) if year else None)

    papers = parse_names(raw_names)

    nodes: dict[str, dict] = {}
    edges: dict[tuple[str, str], int] = {}

    for people, year in zip(papers, years):
        ids: list[str] = []
        for last, first in people:
            if (fold(last), fold(first)) == ME:
                continue
            node_id = slugify(f"{last} {first}") if first else slugify(last)
            display = f"{first} {last}".strip()
            record = nodes.setdefault(
                node_id, {"id": node_id, "name": display, "papers": 0, "firstYear": None}
            )
            record["papers"] += 1
            if year is not None:
                record["firstYear"] = year if record["firstYear"] is None else min(
                    record["firstYear"], year
                )
            # Prefer the fullest spelling seen for the display name.
            if len(display) > len(record["name"]):
                record["name"] = display
            ids.append(node_id)

        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if a == b:
                    continue
                edges[tuple(sorted((a, b)))] = edges.get(tuple(sorted((a, b))), 0) + 1

    urls = load_coauthor_urls()
    for node in nodes.values():
        parts = node["name"].rsplit(" ", 1)
        surname = parts[-1] if parts else node["name"]
        # The display name is "First Last"; recover the surname the same way.
        first = parts[0] if len(parts) > 1 else ""
        record = urls.get(fold(surname))
        if record is None:
            # Two-word surnames, or the surname-only case.
            record = urls.get(fold(node["name"]))
        node["url"] = (record["urls"].get(fold(first)) or record["any"]) if record else None

    return {"nodes": nodes, "edges": edges}


# --------------------------------------------------------------------------
# layout
# --------------------------------------------------------------------------

def layout(nodes: dict[str, dict], edges: dict[tuple[str, str], int]) -> dict[str, tuple[float, float]]:
    """Kamada-Kawai per connected component, then pack, then normalise to [-1, 1].

    Kamada-Kawai on a disconnected graph assigns an effectively infinite
    distance between components, which flings the isolated nodes to the horizon
    and collapses everyone else into a dot. So each component is laid out on its
    own and placed afterwards. Edge weights are co-occurrence counts, and
    Kamada-Kawai reads weights as *distances*, so they are inverted: frequent
    collaborators end up close together.
    """
    if not nodes:
        return {}

    graph = nx.Graph()
    graph.add_nodes_from(sorted(nodes))
    for (a, b), weight in sorted(edges.items()):
        graph.add_edge(a, b, weight=weight, distance=1.0 / weight)

    components = sorted(nx.connected_components(graph), key=lambda c: (-len(c), sorted(c)[0]))
    placed: dict[str, np.ndarray] = {}

    for index, component in enumerate(components):
        subgraph = graph.subgraph(component)
        if len(component) == 1:
            local = {next(iter(component)): np.zeros(2)}
        else:
            local = {
                node: np.asarray(position, dtype=float)
                for node, position in nx.kamada_kawai_layout(subgraph, weight="distance").items()
            }

        points = np.array(list(local.values()))
        span = points.max(axis=0) - points.min(axis=0)
        centre = (points.max(axis=0) + points.min(axis=0)) / 2
        scale = 1.0 / max(span.max(), 1e-9) if len(component) > 1 else 1.0

        if index == 0:
            offset, size = np.zeros(2), 1.0
        else:
            # Satellites ring the main component, largest first, deterministically.
            angle = 2 * np.pi * (index - 1) / max(len(components) - 1, 1)
            offset = 0.85 * np.array([np.cos(angle), np.sin(angle)])
            size = 0.3

        for node, position in local.items():
            placed[node] = (position - centre) * scale * size + offset

    points = np.array([placed[node] for node in sorted(placed)])
    centre = (points.max(axis=0) + points.min(axis=0)) / 2
    # One shared scale factor: a per-axis stretch would distort the geometry
    # Kamada-Kawai just spent its effort getting right.
    extent = max((points.max(axis=0) - points.min(axis=0)).max() / 2, 1e-9)
    return {
        node: tuple(round(float(v), 4) for v in (position - centre) / extent)
        for node, position in placed.items()
    }


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------

def list_owned_repos() -> list[tuple[str, str]]:
    """Every public, non-fork repo on the personal account.

    Enumerating rather than curating matters: the page claims these totals are
    measured, and a hand-picked subset presented as a total is simply wrong. It
    also stops the numbers going stale every time a new repo appears.
    """
    try:
        result = subprocess.run(
            ["gh", "api", "--paginate",
             "users/matteospanio/repos?per_page=100&type=owner",
             "--jq", ".[] | select(.fork == false) | .full_name"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    out = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "/" in line:
            owner, _, name = line.partition("/")
            out.append((owner, name))
    return out


def fetch_github() -> tuple[dict | None, str | None]:
    """All owned public repos plus the research-org ones. Returns (payload, error)."""
    repos: list[dict] = []
    seen: set[str] = set()
    failures = 0

    candidates = list_owned_repos() + EXTRA_REPOS
    if not candidates:
        return None, "could not enumerate repositories"

    for owner, name in candidates:
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{owner}/{name}"],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as error:
            print(f"github: `gh` unavailable ({error})", file=sys.stderr)
            return None, str(error)

        if result.returncode != 0:
            failures += 1
            continue
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            failures += 1
            continue
        if data.get("full_name") in seen:
            continue  # transferred repo, reached under both owners
        seen.add(data.get("full_name"))

        repos.append({
            "name": data.get("name"),
            "fullName": data.get("full_name"),
            "description": data.get("description"),
            "stars": int(data.get("stargazers_count") or 0),
            "forks": int(data.get("forks_count") or 0),
            "language": data.get("language"),
            "topics": sorted(data.get("topics") or []),
            "pushedAt": data.get("pushed_at"),
            "url": data.get("html_url"),
            "archived": bool(data.get("archived")),
        })

    if not repos:
        return None, "no repositories resolved"

    repos.sort(key=lambda r: (-r["stars"], r["fullName"] or ""))
    return {
        "totalStars": sum(r["stars"] for r in repos),
        "totalForks": sum(r["forks"] for r in repos),
        "repos": repos,
    }, (f"{failures} candidate(s) not found" if failures else None)


def fetch_huggingface() -> tuple[dict | None, str | None]:
    """Models and datasets for the csc-unipd org. Returns (payload, error)."""
    def normalise(item: dict, kind: str) -> dict:
        identifier = item.get("id") or ""
        record = {
            "id": identifier,
            "downloads": item.get("downloads"),
            "downloadsAllTime": item.get("downloadsAllTime"),
            "likes": item.get("likes"),
            "lastModified": item.get("lastModified"),
            "url": f"https://huggingface.co/{'' if kind == 'models' else 'datasets/'}{identifier}",
        }
        if kind == "models":
            record["pipelineTag"] = item.get("pipeline_tag")
        return record

    out: dict[str, list[dict]] = {}
    try:
        with httpx.Client(timeout=30, follow_redirects=True,
                          headers={"User-Agent": "matteospanio.github.io footprint builder"}) as client:
            for kind in ("models", "datasets"):
                response = client.get(
                    f"https://huggingface.co/api/{kind}",
                    params={"author": HF_AUTHOR, "full": "true"},
                )
                response.raise_for_status()
                items = response.json()
                out[kind] = sorted(
                    (normalise(item, kind) for item in items),
                    key=lambda r: (-(r["downloads"] or 0), r["id"]),
                )
    except Exception as error:  # noqa: BLE001 - a dead API must not fail the run
        print(f"huggingface unavailable: {error}", file=sys.stderr)
        return None, str(error)

    everything = out["models"] + out["datasets"]
    return {
        "totalDownloads": sum(r["downloads"] or 0 for r in everything),
        "totalDownloadsAllTime": (
            sum(r["downloadsAllTime"] or 0 for r in everything)
            if any(r["downloadsAllTime"] is not None for r in everything) else None
        ),
        "totalLikes": sum(r["likes"] or 0 for r in everything),
        "models": out["models"],
        "datasets": out["datasets"],
    }, None


def read_citations() -> tuple[dict, dict]:
    """(citations block, source status). Local file, so failure means missing."""
    if not CITATIONS.exists():
        return (
            {"total": None, "perYear": {}, "cumulative": {}, "byPaper": [],
             "yearlyCovered": 0, "yearlyCitations": 0},
            {"ok": False, "fetchedAt": None, "error": "citations.json missing"},
        )

    payload = json.loads(CITATIONS.read_text(encoding="utf-8"))
    papers = payload.get("papers", {})
    upstream = payload.get("sources", {})

    per_year: dict[str, int] = {}
    covered = 0
    for record in papers.values():
        counts = record.get("countsByYear") or {}
        if counts:
            covered += 1
        for year, count in counts.items():
            per_year[str(year)] = per_year.get(str(year), 0) + int(count)

    per_year = dict(sorted(per_year.items()))
    running, cumulative = 0, {}
    for year, count in per_year.items():
        running += count
        cumulative[year] = running

    by_paper = sorted(
        (
            {
                "id": key,
                "title": record.get("title"),
                "year": record.get("year"),
                "citations": int(record.get("citations") or 0),
            }
            for key, record in papers.items()
        ),
        key=lambda r: (-r["citations"], r["id"]),
    )

    return (
        {
            "total": sum(r["citations"] for r in by_paper),
            "papers": len(by_paper),
            # The per-year series only covers papers whose source reported it.
            # Charting it as if it were the total would understate by ~2/3.
            "yearlyCovered": covered,
            "yearlyCitations": running,
            "perYear": per_year,
            "cumulative": cumulative,
            "byPaper": by_paper,
        },
        {
            "ok": True,
            "fetchedAt": payload.get("generatedAt"),
            # Most of these counts come from Google Scholar, which blocks
            # datacenter IPs and therefore fails often. When its last fetch
            # failed the numbers were carried forward from an earlier run, and
            # saying so beats presenting stale data as freshly measured.
            "scholarOk": bool(upstream.get("scholar", {}).get("ok")),
            "openalexOk": bool(upstream.get("openalex", {}).get("ok")),
            "stale": not bool(upstream.get("scholar", {}).get("ok")),
            "note": "local file written by update_citations.py",
        },
    )


# --------------------------------------------------------------------------

def main() -> int:
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    previous: dict = {}
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}

    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    graph = build_coauthor_graph(entries)
    positions = layout(graph["nodes"], graph["edges"])

    nodes = []
    for node_id in sorted(graph["nodes"], key=lambda k: (-graph["nodes"][k]["papers"], k)):
        node = dict(graph["nodes"][node_id])
        x, y = positions.get(node_id, (0.0, 0.0))
        node["x"], node["y"] = x, y
        nodes.append(node)

    edges = [
        {"s": a, "t": b, "w": w}
        for (a, b), w in sorted(graph["edges"].items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    citations, citations_source = read_citations()

    github, github_error = fetch_github()
    if github is None:
        stale = previous.get("github")
        github = stale or {"totalStars": None, "totalForks": None, "repos": []}
        github_source = {
            "ok": False, "stale": bool(stale), "error": github_error,
            "fetchedAt": (previous.get("sources", {}).get("github", {}).get("fetchedAt")
                          if stale else None),
        }
    else:
        github_source = {"ok": True, "fetchedAt": now}
        if github_error:
            github_source["note"] = github_error

    huggingface, hf_error = fetch_huggingface()
    if huggingface is None:
        stale = previous.get("huggingface")
        huggingface = stale or {
            "totalDownloads": None, "totalDownloadsAllTime": None,
            "totalLikes": None, "models": [], "datasets": [],
        }
        hf_source = {
            "ok": False, "stale": bool(stale), "error": hf_error,
            "fetchedAt": (previous.get("sources", {}).get("huggingface", {}).get("fetchedAt")
                          if stale else None),
        }
    else:
        hf_source = {"ok": True, "fetchedAt": now}

    payload = {
        "schemaVersion": 1,
        "generatedAt": today,
        "sources": {
            "citations": citations_source,
            "github": github_source,
            "huggingface": hf_source,
            "bibliography": {"ok": True, "fetchedAt": today,
                             "note": f"parsed {len(entries)} entries from papers.bib"},
        },
        "headline": {
            "publications": len(entries),
            "citations": citations["total"],
            "coauthors": len(nodes),
            "repos": len(github["repos"]) if github.get("repos") else None,
            "stars": github.get("totalStars"),
            "hfDownloads": huggingface.get("totalDownloads"),
        },
        "citations": citations,
        "github": github,
        "huggingface": huggingface,
        "coauthors": {
            "me": slugify(f"{ME[0]} {ME[1]}"),
            "nodes": nodes,
            "edges": edges,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    head = payload["headline"]
    print(
        f"wrote {OUT.relative_to(ROOT)}: {head['publications']} pubs, "
        f"{head['citations']} citations, {head['coauthors']} coauthors "
        f"({len(edges)} edges), {head['repos'] or 0} repos / {head['stars']} stars, "
        f"{head['hfDownloads']} HF downloads "
        f"[github {'ok' if github_source['ok'] else 'FAILED'}, "
        f"hf {'ok' if hf_source['ok'] else 'FAILED'}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
