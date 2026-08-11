#!/usr/bin/env python3
"""Build the publications word cloud from the LaTeX sources of the published papers.

The archives live outside the repository (they contain figures and, in one case,
unpublished work), so this is run by hand and its output is committed:

    python scripts/build_wordcloud.py

Two things are worth knowing about the approach.

*Scoring is breadth-first.* A term is ranked by how many separate papers use it,
not by how often it appears, so a single paper cannot push its own jargon to the
top and the cloud describes the body of work rather than the longest document.

*The layout is computed here, exactly.* The cloud is set in JetBrains Mono, whose
advance width is exactly 0.6 em for every glyph, so a word's box is known from
its character count alone. That means the packing can be solved in Python and
shipped as static SVG — no measuring pass, no layout library, no JavaScript.
"""

from __future__ import annotations

import json
import math
import re
import sys
import tarfile
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "viz" / "wordcloud.json"

PAPERS_DIR = (
    Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Scrivania" / "papers"
)

# Not published work: excluded on purpose. Anything else in the directory that is
# a .zip is treated as a published paper.
EXCLUDE = {
    "2026_internal_tech_report.zip",
    # A PLOS ONE submission rather than a published paper — add it here once it is out.
    "2026_plos_one.tar.gz",
}

# --- layout -----------------------------------------------------------------

WORDS = 80
NARROW_WORDS = 34  # what stays legible when the same cloud is 390px wide
UNIGRAMS, BIGRAMS = 62, 26
PHRASE_WEIGHT = 2.4  # lifts phrases into the visible bands; tuned by eye
SIZE_MIN, SIZE_MAX = 11.0, 62.0
ADVANCE = 0.6  # JetBrains Mono advance width, in em
LINE_HEIGHT = 1.05
PAD_X, PAD_Y = 0.42, 0.26  # gap between boxes, in em of the word's own size
ASPECT = 2.05  # spiral is stretched horizontally so the cloud fills a wide box

# --- text extraction --------------------------------------------------------

SKIP_SUFFIXES = {".cls", ".sty", ".bst", ".bib", ".clo", ".def"}

# Environments whose contents are not prose: numbers, file paths and code.
DROP_ENVIRONMENTS = (
    "figure",
    "figure*",
    "table",
    "table*",
    "tabular",
    "tabularx",
    "longtable",
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "eqnarray",
    "displaymath",
    "math",
    "verbatim",
    "lstlisting",
    "minted",
    "algorithm",
    "algorithmic",
    "thebibliography",
    "tikzpicture",
    "filecontents",
)

# Commands whose braced argument is a path, a key or a number — never words.
DROP_WITH_ARG = (
    "cite",
    "citep",
    "citet",
    "citeauthor",
    "citeyear",
    "autocite",
    "textcite",
    "ref",
    "eqref",
    "autoref",
    "cref",
    "Cref",
    "pageref",
    "label",
    "includegraphics",
    "input",
    "include",
    "bibliography",
    "bibliographystyle",
    "usepackage",
    "documentclass",
    "newcommand",
    "renewcommand",
    "def",
    "url",
    "hypersetup",
    "geometry",
    "setlength",
    "definecolor",
    "color",
    "textcolor",
    "graphicspath",
    "orcid",
    "email",
    "affiliation",
    "institute",
    "acmConference",
    "acmDOI",
    "acmISBN",
    "keywords",
    "ccsdesc",
    "pdfstring",
)

STOPWORDS = set("""
a about above across after again against all almost also although always among an and another any
anything are around as at
back be became because become becomes been before being below best better between beyond both but by
came can cannot could
did do does doing done down due during
each early either else enough especially et etc even ever every
few first five for former four from further
gave get give given gives go
had has have having he hence her here hers herself him himself his how however
i if in indeed instead into is it its itself
just
keep kept
last later latter least less let like likely
made mainly make makes many may me might more moreover most mostly much must my myself
namely near nearly need neither never nevertheless next no nor not nothing now
obtained of off often on once one only onto or other others otherwise our ours ourselves out over own
particular particularly per perhaps possible presented previously
quite
rather really regarding respectively
said same second see seem seems seen several shall she should show showed shown shows since so some
something still such
take taken than that the their theirs them themselves then there therefore these they third this those
though three through thus to together too toward towards two
under unless until up upon us use used useful uses using usually
various very via
was way we well were what when where whereas whether which while who whom whose why will with within
without would
yet you your yours
""".split())

# Boilerplate that survives the stripping: LaTeX leftovers, paper furniture and
# words every paper in every field uses.
STOPWORDS |= set("""
abstract acknowledgements appendix begin bib caption center centering cite citep column conference
copyright doi documentclass emph end eqref fig figs figure figures footnote hline href hspace input
item itemize includegraphics label large left linewidth listing maketitle multicolumn newpage
noindent onecolumn pagestyle par paragraph paren pdf ref right section sec seealso setlength small
subsection subsubsection tab table tables textbf textit texttt textwidth thanks tikz title toprule
twocolumn usepackage vspace midrule bottomrule ldots dots emph url textsc author authors univ
university department institute email address keywords keyword acmformat acknowledgment
approach approaches area areas aspect aspects author available based case cases chapter compared
consider considered consists contains context contribution contributions corresponding current
data dataset datasets defined definition described describes description detail details different
discussed discussion effect effects example examples experiment experiments field final finally
following form found framework function functions general given goal group groups high higher
importance important include included includes including increase individual information initial
introduction issue issues level levels limited main method methodology methods number numbers
observed obtained order overview paper papers part particular performance possible present presents
previous problem problems procedure process proposed provide provided provides purpose question
range rate ratio related report reported represent representation research respect result results
role sample samples section select selected set sets significant significantly similar single
specific standard state step steps studied studies study subject subjects summary support system
systems table term terms test tested tests thesis time times total type types understanding unit
units value values version way work works file command document
""".split())

# Institutional and typesetting residue that survives on affiliation lines and in
# running text, and reads as vocabulary without being any.
STOPWORDS |= set("""
csc dei unipd padova padua italy italia university universita equation equations new output
inputs outputs figure figures section sections chapter subsection appendix appendices
template templates name names class classes
""".split())

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]{2,}")

# Terms that mean the same thing written two ways. Applied after normalisation.
SYNONYMS = {
    "neural-network": "neural network",
    "deep-learning": "deep learning",
    "state-of-the-art": "state of the art",
    "large language model": "large language models",
    "language model": "language models",
    "convolutional neural": "neural networks",
    "neural network": "neural networks",
    "audio recording": "audio recordings",
    "magnetic tapes": "magnetic tape",
    "cultural heritages": "cultural heritage",
    "musical instrument": "musical instruments",
    "sound design": "sound design",
    "signal processing": "signal processing",
    "preservation audio": "preservation",
    "magnetic tape": "tape",
    "video analyzer": "video",
    "audio signal": "signal",
    "programming language": "language",
}

# Acronyms and proper nouns that should not be lowercased in the rendered cloud.
CASING = {
    "lilypond": "LilyPond",
    "musicxml": "MusicXML",
    "musicgen": "MusicGEN",
    "midi": "MIDI",
    "mpai": "MPAI",
    "llm": "LLM",
    "llms": "LLMs",
    "gpt": "GPT",
    "cnn": "CNN",
    "stft": "STFT",
    "fft": "FFT",
    "gpu": "GPU",
    "mir": "MIR",
    "clap": "CLAP",
    "pytorch": "PyTorch",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "torchfx": "TorchFX",
    "ieee": "IEEE",
    "aes": "AES",
    "eeg": "EEG",
    "svm": "SVM",
    "rnn": "RNN",
    "lstm": "LSTM",
    "vae": "VAE",
    "gan": "GAN",
    "api": "API",
    "dsp": "DSP",
    "ai": "AI",
    "arp": "ARP",
    "cae": "CAE",
    "xml": "XML",
    "wav": "WAV",
}


def read_archive(path: Path) -> list[str]:
    """Every .tex member of an archive, kept separate.

    Separate matters: the preamble is cut at \\begin{document}, and concatenating
    first would leave every later file's preamble in the text.
    """
    parts: list[str] = []

    def keep(name: str) -> bool:
        low = name.lower()
        if not low.endswith(".tex"):
            return False
        return Path(low).suffix not in SKIP_SUFFIXES

    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            for member in z.namelist():
                if keep(member):
                    parts.append(z.read(member).decode("utf-8", "ignore"))
    else:
        with tarfile.open(path) as t:
            for member in t.getmembers():
                if member.isfile() and keep(member.name):
                    handle = t.extractfile(member)
                    if handle:
                        parts.append(handle.read().decode("utf-8", "ignore"))

    return parts


def strip_latex(text: str) -> str:
    # Comments first: a stray % inside a later regex would swallow real text.
    text = re.sub(r"(?<!\\)%.*", " ", text)

    # Preamble. Section files have no \begin{document} and are kept whole.
    if r"\begin{document}" in text:
        text = text.split(r"\begin{document}", 1)[1]
    text = text.split(r"\end{document}", 1)[0]

    for env in DROP_ENVIRONMENTS:
        text = re.sub(
            r"\\begin\{" + re.escape(env) + r"\}.*?\\end\{" + re.escape(env) + r"\}",
            " ",
            text,
            flags=re.S,
        )

    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    text = re.sub(r"(?<!\\)\$.*?(?<!\\)\$", " ", text, flags=re.S)
    text = re.sub(r"\\\[.*?\\\]", " ", text, flags=re.S)
    text = re.sub(r"\\\(.*?\\\)", " ", text, flags=re.S)

    # Environment names are markup, not prose: \begin{itemize} must not leave "itemize".
    text = re.sub(r"\\(begin|end)\s*\{[^{}]*\}", " ", text)

    # \href{url}{label} keeps the label; the rest lose their argument entirely.
    text = re.sub(r"\\href\s*\{[^{}]*\}\s*\{([^{}]*)\}", r" \1 ", text)
    for cmd in DROP_WITH_ARG:
        # (?![A-Za-z]) is load-bearing: without it \bibliography eats the front of
        # \bibliographystyle and leaves "style" behind as a top-ranked term.
        text = re.sub(
            r"\\" + cmd + r"(?![A-Za-z])\s*(\[[^\]]*\])?\s*(\{[^{}]*\})*", " ", text
        )

    # Whatever commands remain are formatting: drop the command, keep the text.
    text = re.sub(r"\\[A-Za-z@]+\*?\s*(\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}~^_&#]", " ", text)
    text = text.replace("\\", " ")

    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def singular(word: str) -> str:
    """Light plural folding. Deliberately conservative: 'analysis' must survive."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if (
        len(word) > 4
        and word.endswith("s")
        and not word.endswith(("ss", "us", "is", "as"))
    ):
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    """Words, with an empty string wherever a phrase cannot legally continue.

    Punctuation has to break the sequence: without it "…for preservation. Audio
    documents…" contributes the phrase "preservation audio", which nobody wrote.
    """
    out: list[str] = []
    for chunk in re.split(r"[^A-Za-z\s'\-]+", text):
        for raw in WORD_RE.findall(chunk):
            word = raw.lower().strip("-'")
            if len(word) < 3 or word in STOPWORDS:
                out.append("")  # a stop word breaks a phrase too
                continue
            out.append(singular(word))
        out.append("")
    return out


def people() -> set[str]:
    """Author names, from the site's own bibliography.

    Coauthors are named in acknowledgements and running heads often enough to
    rank, and a cloud of colleagues' surnames says nothing about the research.
    """
    names: set[str] = set()
    bib = ROOT / "src" / "data" / "papers.bib"
    if not bib.exists():
        return names
    for field in re.findall(
        r"author\s*=\s*\{(.+?)\}\s*,\s*\n", bib.read_text("utf-8"), re.S
    ):
        cleaned = unicodedata.normalize(
            "NFKD", field.replace("{", " ").replace("}", " ")
        )
        cleaned = "".join(c for c in cleaned if not unicodedata.combining(c))
        for part in re.split(r"\band\b|,", cleaned):
            for word in WORD_RE.findall(part):
                if len(word) > 2:
                    names.add(word.lower())
    return names


def collect(paths: list[Path]) -> tuple[Counter, Counter, int]:
    """Total frequency and document frequency, over unigrams and bigrams."""
    total: Counter = Counter()
    document: Counter = Counter()

    for path in paths:
        tokens: list[str] = []
        for part in read_archive(path):
            # The empty string is the bigram breaker, so files cannot bleed into
            # each other and produce a phrase that was never written.
            tokens.extend(tokenize(strip_latex(part)))
            tokens.append("")

        here: Counter = Counter()

        for token in tokens:
            if token:
                here[token] += 1

        for a, b in zip(tokens, tokens[1:]):
            if a and b:
                here[f"{a} {b}"] += 1

        for term, n in here.items():
            total[term] += n
            document[term] += 1

    return total, document, len(paths)


def merge_synonyms(total: Counter, document: Counter) -> None:
    for src, dst in SYNONYMS.items():
        if src in total and src != dst:
            total[dst] += total.pop(src)
            document[dst] = max(document.get(dst, 0), document.pop(src, 0))


def score(total: Counter, document: Counter, papers: int) -> list[dict]:
    """Depth first, breadth second.

    Ranking by document frequency alone puts "evaluation", "new" and "conclusion"
    on top: every paper says them once. What distinguishes a subject term is that
    a paper using it uses it *repeatedly*, so the primary signal is mean uses per
    paper, with document frequency as a square-root damped multiplier so a term
    still has to appear across the body of work.
    """
    unigrams: list[dict] = []
    bigrams: list[dict] = []

    for term, tf in total.items():
        df = document[term]
        phrase = " " in term
        if df < 4 or tf < (8 if phrase else 20):
            continue
        item = {
            "text": term,
            "tf": tf,
            "df": df,
            "score": (tf / df) * (df / papers) ** 0.5,
        }
        (bigrams if phrase else unigrams).append(item)

    unigrams.sort(key=lambda item: -item["score"])
    bigrams.sort(key=lambda item: -item["score"])

    # Phrases carry the actual subject matter ("cultural heritage" says far more
    # than "cultural" and "heritage" scattered apart), and they are inherently
    # rarer than their parts, so they are selected under their own quota rather
    # than competing directly with single words.
    chosen = unigrams[:UNIGRAMS] + bigrams[:BIGRAMS]

    # Drop a single word that is mostly just half of a phrase already shown.
    absorbed = {
        half
        for phrase in bigrams[:BIGRAMS]
        for half in phrase["text"].split()
        for item in unigrams[:UNIGRAMS]
        if item["text"] == half and phrase["tf"] >= 0.6 * item["tf"]
    }

    for item in chosen:
        if " " in item["text"]:
            item["score"] *= PHRASE_WEIGHT

    chosen = [item for item in chosen if item["text"] not in absorbed]
    chosen.sort(key=lambda item: -item["score"])
    return chosen[:WORDS]


def pretty(term: str) -> str:
    return " ".join(CASING.get(part, part) for part in term.split())


def lay_out(
    words: list[dict],
    size_min: float = SIZE_MIN,
    size_max: float = SIZE_MAX,
    aspect: float = ASPECT,
) -> dict:
    """Archimedean spiral packing with exact monospace boxes.

    Parameterised because one layout cannot serve both widths: scaled down to a
    phone, the desktop cloud renders its smallest terms at about four pixels.
    """
    top = words[0]["score"]
    bottom = words[-1]["score"]
    span = (top - bottom) or 1.0

    placed: list[dict] = []
    boxes: list[tuple[float, float, float, float]] = []

    for index, word in enumerate(words):
        # Perceptual sizing: rank drives the size more evenly than the raw score,
        # which is long-tailed and would leave everything below rank 10 tiny.
        by_score = (word["score"] - bottom) / span
        by_rank = 1 - index / max(len(words) - 1, 1)
        weight = 0.35 * by_score + 0.65 * by_rank
        size = size_min + (size_max - size_min) * weight**1.7

        label = pretty(word["text"])
        width = len(label) * ADVANCE * size
        height = size * LINE_HEIGHT
        gap_x = size * PAD_X
        gap_y = size * PAD_Y

        step = 0.28 + size * 0.05
        angle = 0.0
        x = y = 0.0
        for _ in range(60000):
            radius = step * angle / (2 * math.pi)
            x = math.cos(angle) * radius * aspect
            y = math.sin(angle) * radius
            box = (
                x - width / 2 - gap_x / 2,
                y - height / 2 - gap_y / 2,
                x + width / 2 + gap_x / 2,
                y + height / 2 + gap_y / 2,
            )
            if not any(
                box[0] < other[2]
                and other[0] < box[2]
                and box[1] < other[3]
                and other[1] < box[3]
                for other in boxes
            ):
                boxes.append(box)
                break
            angle += 0.12 + 0.55 / (1 + radius / 40)
        else:
            continue

        placed.append(
            {
                "text": label,
                "x": round(x, 2),
                "y": round(y, 2),
                "w": round(width, 2),
                "size": round(size, 2),
                "df": word["df"],
                "tf": word["tf"],
                # Four bands drive colour and weight in the SVG.
                "tier": min(3, int(weight * 4)),
            }
        )

    pad = 12
    left = min(box[0] for box in boxes) - pad
    topmost = min(box[1] for box in boxes) - pad
    right = max(box[2] for box in boxes) + pad
    bottommost = max(box[3] for box in boxes) + pad

    return {
        "words": placed,
        "viewBox": [
            round(left, 1),
            round(topmost, 1),
            round(right - left, 1),
            round(bottommost - topmost, 1),
        ],
    }


def main() -> int:
    if not PAPERS_DIR.is_dir():
        print(f"no such directory: {PAPERS_DIR}", file=sys.stderr)
        return 1

    paths = sorted(
        p for p in PAPERS_DIR.iterdir() if p.suffix == ".zip" and p.name not in EXCLUDE
    )
    if not paths:
        print(f"no paper archives in {PAPERS_DIR}", file=sys.stderr)
        return 1

    STOPWORDS.update(people())

    total, document, papers = collect(paths)
    merge_synonyms(total, document)
    words = score(total, document, papers)

    layout = lay_out(words)
    # A phone gets its own pack: fewer terms, a near-square spiral and a much
    # higher floor on the type size, because the desktop cloud scaled to 390px
    # renders its tail at about four pixels.
    narrow = lay_out(words[:NARROW_WORDS], size_min=13.0, size_max=40.0, aspect=0.92)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "papers": papers,
                "sources": [p.name for p in paths],
                "terms": len(layout["words"]),
                **layout,
                "narrow": narrow,
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"{papers} papers -> {len(layout['words'])} terms "
        f"({len(narrow['words'])} narrow) -> {OUT.relative_to(ROOT)}"
    )
    print("top: " + ", ".join(w["text"] for w in layout["words"][:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
