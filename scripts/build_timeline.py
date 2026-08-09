#!/usr/bin/env python3
"""Build src/data/viz/timeline.json — the model behind the CSS Grid timeline.

The component that consumes this file places things on a grid of months and draws
no axes of its own, so every date here has to be a clean YYYY-MM. That is the whole
difficulty: papers.bib records only a year, and a year is not a position.

Where months come from, in the order the resolver tries them:

  1. scripts/data/event_dates.yml — hand-curated, each line carrying the evidence
     for the month it asserts (conference dates, defence dates from resume.json,
     publisher records). This is the only place a human writes a date.
  2. The arXiv identifier. A modern arXiv id encodes YYMM of the first posting, so
     `arxiv = {2604.10628}` is April 2026 by construction, not by guesswork.
  3. The year's midpoint, tagged `"approx": true`. The component is expected to
     render approximate events differently; the alternative — a confident-looking
     date nobody can defend — is the failure mode this whole file exists to avoid.

News, blog posts and resume spans already carry real dates and are read verbatim.

Only one source is remote: the GitHub release history for the four repositories
listed under `software:` in the curated file, read through `gh api`. If gh is
missing, unauthenticated or offline, the previous file's software events are
carried forward and `sources.github.ok` is set to false — never invented, never
silently dropped.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "viz" / "timeline.json"
BIB = ROOT / "src" / "data" / "papers.bib"
RESUME = ROOT / "src" / "data" / "resume.json"
CURATED = Path(__file__).resolve().parent / "data" / "event_dates.yml"
NEWS_DIR = ROOT / "src" / "content" / "news"
BLOG_DIR = ROOT / "src" / "content" / "blog"
PROJECT_DIR = ROOT / "src" / "content" / "projects"

SCHEMA_VERSION = 1

LANES = [
    {"id": "papers", "label": "Publications", "color": "#5eead4"},
    {"id": "software", "label": "Software & models", "color": "#4ade80"},
    {"id": "talks", "label": "Conferences & talks", "color": "#c084fc"},
    {"id": "writing", "label": "Writing", "color": "#7dd3fc"},
    # Spans live in their own lane; the four above hold point events.
    {"id": "life", "label": "Positions & study", "color": "#fbbf24"},
]

THEMES = {
    "cultural-heritage",
    "multimodal",
    "symbolic-music",
    "dsp-tooling",
    "musicology",
    "engineering",
}

# News kinds map onto lanes: a model or library announcement is a software event,
# everything else (acceptances, conferences, invited talks) is a venue event.
NEWS_LANE = {"release": "software"}

MIDPOINT_MONTH = "07"


# --------------------------------------------------------------------------- utils


def slugify(text: str) -> str:
    """A DOM-id-safe token. Bib keys include DOIs and raw URLs, so `#anchor` links
    to /publications/ cannot use the key verbatim."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text)).strip("-")


def month(value: str) -> str:
    """Any ISO-ish date down to its YYYY-MM prefix."""
    return str(value)[:7]


def month_key(value: str) -> tuple[int, int]:
    year, mon = value.split("-")[:2]
    return int(year), int(mon)


def frontmatter(path: Path) -> dict[str, Any]:
    """The YAML block between the leading `---` fences. Returns {} if absent."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def check_theme(value: Any, where: str, problems: list[str]) -> str | None:
    if value is None:
        return None
    if value not in THEMES:
        problems.append(f"{where}: unknown theme {value!r}")
        return None
    return value


# ------------------------------------------------------------------------- sources


def read_bibliography() -> list[dict[str, Any]]:
    """One dict per @entry, with only the fields the timeline needs."""
    text = BIB.read_text(encoding="utf-8")
    entries: list[dict[str, Any]] = []

    for match in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        kind, key, body = match.group(1).lower(), match.group(2).strip(), match.group(3)

        title_match = re.search(r"title\s*=\s*\{(.+?)\}\s*,?\s*\n", body, re.S)
        title = ""
        if title_match:
            title = re.sub(
                r"\s+", " ", title_match.group(1).replace("{", "").replace("}", "")
            ).strip()

        year_match = re.search(r"\byear\s*=\s*\{?\s*(\d{4})", body)
        arxiv_match = re.search(r"\barxiv\s*=\s*\{([^}]+)\}", body)
        abbr_match = re.search(r"\babbr\s*=\s*\{([^}]+)\}", body)

        entries.append(
            {
                "key": key,
                "type": kind,
                "title": title,
                "year": int(year_match.group(1)) if year_match else None,
                "arxiv": arxiv_match.group(1).strip() if arxiv_match else None,
                "abbr": abbr_match.group(1).strip() if abbr_match else None,
            }
        )

    return entries


def arxiv_month(identifier: str | None) -> str | None:
    """Modern arXiv ids are YYMM.NNNNN — the month is part of the identifier."""
    if not identifier:
        return None
    match = re.match(r"^(\d{2})(\d{2})\.\d{4,5}(v\d+)?$", identifier.strip())
    if not match:
        return None
    yy, mm = int(match.group(1)), int(match.group(2))
    if not 1 <= mm <= 12:
        return None
    return f"20{yy:02d}-{mm:02d}"


def read_news() -> list[dict[str, Any]]:
    items = []
    for path in sorted(NEWS_DIR.glob("*.md")):
        data = frontmatter(path)
        if not data.get("date"):
            continue
        items.append({"id": path.stem, "data": data})
    return items


def read_blog() -> list[dict[str, Any]]:
    items = []
    for path in sorted(BLOG_DIR.glob("*/index.md*")):
        data = frontmatter(path)
        if not data.get("date"):
            continue
        items.append({"id": path.parent.name, "data": data})
    return items


def read_projects() -> dict[str, dict[str, Any]]:
    """Slug -> frontmatter, used to give software events a page to link to."""
    out = {}
    for path in sorted(PROJECT_DIR.glob("*/index.md*")):
        out[path.parent.name] = frontmatter(path)
    return out


def read_resume_spans(curated: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    """Work and education entries become spans in the `life` lane."""
    resume = json.loads(RESUME.read_text(encoding="utf-8"))
    labels = curated.get("spans", {}) or {}
    spans = []

    for section in ("work", "education"):
        for item in resume.get(section, []):
            start = item.get("startDate")
            if not start:
                continue

            lookup = labels.get(f"{section}:{start}", {})
            institution = item.get("institution") or item.get("company") or item.get("name") or ""
            role = item.get("position") or item.get("studyType") or ""
            fallback_label = " — ".join(part for part in (role, institution) if part)

            end_raw = item.get("endDate") or ""
            spans.append(
                {
                    "id": lookup.get("id") or slugify(f"{section}-{role}-{institution}")[:48],
                    "lane": "life",
                    "kind": section,
                    "start": month(start),
                    "end": month(end_raw) if end_raw else None,
                    "ongoing": not end_raw,
                    "label": lookup.get("label") or fallback_label,
                    "url": item.get("url"),
                }
            )
            if not lookup:
                problems.append(f"resume {section}:{start}: no curated label, using fallback")

    return spans


def gh_json(endpoint: str) -> Any:
    result = subprocess.run(
        ["gh", "api", endpoint, "--paginate"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip().splitlines()[-1] if result.stderr else "gh failed")
    # --paginate concatenates one JSON document per page.
    chunks = re.sub(r"\]\s*\[", ",", result.stdout.strip())
    return json.loads(chunks)


def fetch_github(repos: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """{repo: {createdAt, releases: [...]}} or ({}, error). Never raises."""
    out: dict[str, Any] = {}
    for name in repos:
        try:
            meta = gh_json(f"repos/{name}")
            releases = gh_json(f"repos/{name}/releases?per_page=100")
        except Exception as error:  # noqa: BLE001 - a dead API must not fail the build
            return {}, f"{name}: {error}"
        out[name] = {
            "createdAt": meta.get("created_at"),
            "releases": [
                {
                    "tag": r.get("tag_name"),
                    "publishedAt": r.get("published_at") or r.get("created_at"),
                    "prerelease": bool(r.get("prerelease")),
                    "url": r.get("html_url"),
                }
                for r in (releases or [])
                if r.get("tag_name") and (r.get("published_at") or r.get("created_at"))
            ],
            "url": meta.get("html_url"),
        }
    return out, None


# -------------------------------------------------------------------- event builders


def version_tuple(tag: str) -> tuple[int, ...] | None:
    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        return None
    return tuple(int(g) for g in match.groups())


def software_events(
    github: dict[str, Any], curated_sw: dict[str, Any], projects: dict[str, Any]
) -> list[dict[str, Any]]:
    """First release per repo, plus minor/major milestones and the latest release.

    Patch releases are dropped: at month resolution a run of v0.7.1-style fixes is
    noise, and several of them land in the same grid cell anyway. Whatever survives
    is then collapsed to one event per repo-month, preferring a stable tag over a
    prerelease so that a v0.1.0rc published six days before v0.1.0 does not become
    the visible "first release".
    """
    events: list[dict[str, Any]] = []

    for name, meta in curated_sw.items():
        repo = github.get(name)
        if not repo:
            continue

        label = meta.get("label") or name.split("/")[-1]
        theme = meta.get("theme")
        project = meta.get("project")
        page = f"/projects/{project}/" if project in projects else repo.get("url")

        releases = sorted(repo["releases"], key=lambda r: r["publishedAt"])
        if not releases:
            created = repo.get("createdAt")
            if created:
                events.append(
                    {
                        "id": f"{meta['id']}-repo",
                        "lane": "software",
                        "date": month(created),
                        "kind": "repo",
                        "title": f"{label} — repository opened",
                        "url": page,
                        "theme": theme,
                        "approx": False,
                        "repo": name,
                        "note": "no tagged release yet; date is the repository creation date",
                    }
                )
            continue

        first = releases[0]
        latest = releases[-1]
        keep = {id(first), id(latest)}
        for release in releases:
            version = version_tuple(release["tag"])
            if version and version[2] == 0 and not release["prerelease"]:
                keep.add(id(release))
        selected = [r for r in releases if id(r) in keep]

        # One event per month; a stable tag outranks a prerelease in the same cell.
        by_month: dict[str, dict[str, Any]] = {}
        for release in selected:
            cell = month(release["publishedAt"])
            held = by_month.get(cell)
            if held is None or (held["prerelease"] and not release["prerelease"]):
                by_month[cell] = release
            elif held["prerelease"] == release["prerelease"]:
                by_month[cell] = release  # later publication in the same month

        first_month = month(first["publishedAt"])
        for cell, release in sorted(by_month.items()):
            is_first = cell == first_month
            events.append(
                {
                    "id": f"{meta['id']}-{slugify(release['tag'])}",
                    "lane": "software",
                    "date": cell,
                    "kind": "release",
                    "title": f"{label} {release['tag']}"
                    + (" — first release" if is_first else ""),
                    "url": page,
                    "theme": theme,
                    "approx": False,
                    "repo": name,
                    "tag": release["tag"],
                    "releaseUrl": release.get("url"),
                }
            )

    return events


def paper_events(
    bib: list[dict[str, Any]],
    curated_papers: dict[str, Any],
    problems: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    kinds = {"thesis": "thesis", "misc": "score"}
    events, uncurated = [], []

    for entry in bib:
        key = entry["key"]
        meta = curated_papers.get(key) or {}
        if not meta:
            uncurated.append(key)

        theme = check_theme(meta.get("theme"), f"papers.bib:{key}", problems)
        event_id = slugify(key)

        resolved = meta.get("date")
        source = "curated"
        if not resolved:
            resolved, source = arxiv_month(entry["arxiv"]), "arxiv-id"
        approx = False
        if not resolved:
            if not entry["year"]:
                problems.append(f"papers.bib:{key}: no year and no curated date; skipped")
                continue
            resolved, source, approx = f"{entry['year']}-{MIDPOINT_MONTH}", "year-midpoint", True

        events.append(
            {
                "id": event_id,
                "lane": "papers",
                "date": resolved,
                "kind": kinds.get(entry["type"], "paper"),
                "title": entry["title"] or key,
                "url": f"/publications/#{event_id}",
                "theme": theme,
                "approx": approx,
                "bibkey": key,
                "venue": entry["abbr"],
                "dateSource": source,
                **({"note": meta["note"]} if meta.get("note") else {}),
            }
        )

    return events, uncurated


def news_events(
    news: list[dict[str, Any]], curated_news: dict[str, Any], problems: list[str]
) -> list[dict[str, Any]]:
    events = []
    for item in news:
        data = item["data"]
        kind = data.get("kind", "misc")
        theme = check_theme(curated_news.get(item["id"]), f"news/{item['id']}", problems)
        if item["id"] not in curated_news:
            problems.append(f"news/{item['id']}: no curated theme")

        events.append(
            {
                "id": f"news-{slugify(item['id'])}",
                "lane": NEWS_LANE.get(kind, "talks"),
                "date": month(str(data["date"])),
                "kind": kind,
                "title": data.get("title") or item["id"],
                "url": data.get("url") or "/news/",
                "theme": theme,
                # The frontmatter date is when the announcement was written, not
                # when the conference happened — DAFx-25 was announced on 28 Aug
                # and held 2-6 Sept. Mark these as approximate so the marker does
                # not claim a precision it does not have.
                "approx": True,
            }
        )
    return events


def blog_events(blog: list[dict[str, Any]], problems: list[str]) -> list[dict[str, Any]]:
    events = []
    for item in blog:
        data = item["data"]
        if data.get("draft"):
            continue
        published = str(data["date"])
        slug = data.get("slug") or item["id"]
        events.append(
            {
                "id": f"post-{slugify(slug)}",
                "lane": "writing",
                "date": month(published),
                "kind": "post",
                "title": data.get("title") or slug,
                "url": f"/blog/{published[:4]}/{slug}/",
                "theme": check_theme(data.get("theme"), f"blog/{slug}", problems),
                "approx": False,
            }
        )
    return events


# ----------------------------------------------------------------------------- main


def main() -> int:
    problems: list[str] = []
    today = date.today().isoformat()

    curated = yaml.safe_load(CURATED.read_text(encoding="utf-8")) or {}
    curated_papers = curated.get("papers", {}) or {}
    curated_news = curated.get("news", {}) or {}
    curated_sw = curated.get("software", {}) or {}

    previous_doc: dict[str, Any] = {}
    if OUT.exists():
        try:
            previous_doc = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            problems.append(f"{OUT.name} was unreadable; rebuilt from scratch")
    bib = read_bibliography()
    news = read_news()
    blog = read_blog()
    projects = read_projects()

    events: list[dict[str, Any]] = []
    papers, uncurated = paper_events(bib, curated_papers, problems)
    events += papers
    events += news_events(news, curated_news, problems)
    events += blog_events(blog, problems)

    github, gh_error = fetch_github(curated_sw)
    if gh_error:
        problems.append(f"GitHub unavailable: {gh_error}")
        # Stale-but-true beats invented: carry the last good release history forward.
        # `repo` is the marker of a GitHub-derived event — the software lane also
        # holds model announcements read from news, which have already been emitted
        # above and must not be duplicated.
        seen = {e["id"] for e in events}
        events += [
            dict(e)
            for e in previous_doc.get("events", [])
            if e.get("lane") == "software" and e.get("repo") and e.get("id") not in seen
        ]
    else:
        events += software_events(github, curated_sw, projects)

    spans = read_resume_spans(curated, problems)

    months = [e["date"] for e in events] + [s["start"] for s in spans]
    months += [s["end"] for s in spans if s.get("end")]
    if not months:
        print("nothing to place on the timeline; refusing to write", file=sys.stderr)
        return 1
    start = min(months, key=month_key)
    # The grid needs a right edge; run it to the end of the last year in play so an
    # ongoing span has somewhere to end.
    end = f"{max(months, key=month_key)[:4]}-12"

    for span in spans:
        if span["end"] is None:
            span["end"] = end

    events.sort(key=lambda e: (month_key(e["date"]), e["lane"], e["id"]))
    spans.sort(key=lambda s: (month_key(s["start"]), s["id"]))

    lane_counts = {lane["id"]: 0 for lane in LANES}
    for event in events:
        lane_counts[event["lane"]] = lane_counts.get(event["lane"], 0) + 1
    approx_count = sum(1 for e in events if e.get("approx"))

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": today,
        "range": {"start": start, "end": end},
        "lanes": LANES,
        "counts": {"events": len(events), "spans": len(spans), "approx": approx_count,
                   "byLane": lane_counts},
        "sources": {
            "bibliography": {"ok": True, "path": "src/data/papers.bib",
                             "entries": len(bib), "curatedDates": len(curated_papers),
                             "uncurated": uncurated},
            "curatedDates": {"ok": CURATED.exists(), "path": "scripts/data/event_dates.yml"},
            "news": {"ok": True, "path": "src/content/news", "entries": len(news)},
            "blog": {"ok": True, "path": "src/content/blog", "entries": len(blog)},
            "resume": {"ok": RESUME.exists(), "path": "src/data/resume.json",
                       "spans": len(spans)},
            "github": {
                "ok": gh_error is None,
                "fetchedAt": today if gh_error is None else None,
                "repos": sorted(curated_sw),
                "error": gh_error,
                "carriedForward": bool(gh_error),
            },
        },
        "problems": problems,
        "spans": spans,
        "events": events,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lanes = ", ".join(f"{k} {v}" for k, v in lane_counts.items() if v)
    print(
        f"wrote {OUT.relative_to(ROOT)}: {len(events)} events ({lanes}), "
        f"{len(spans)} spans, {approx_count} approximate, "
        f"{start}..{end}, github {'ok' if gh_error is None else 'DOWN'}"
    )
    for problem in problems:
        print(f"  · {problem}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
