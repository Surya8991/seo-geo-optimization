#!/usr/bin/env python3
"""
Automated QA gate for an optimized page's HTML.

Runs the mechanical checks so nothing ships that breaks a hard rule. Manual checks
(flow, factual accuracy, 50-point re-score, source spot-checks) still have to be
done by hand. Brand name, domain and the geo-slug list all come from config.json,
so there is no brand hard-coded here.

Usage:
    python optimizer/qa_check.py "final output/some-page-green.html" --words 3200
    python optimizer/qa_check.py "final output/new-post.html" --words 1800 --new

Optimize mode (default) expects green/red review markers and an end changes-summary
table. --new mode is for a brand-new blog: clean publish-ready HTML, no diff markers.
A Flesch reading-ease score is reported as guidance (target 60+).

Exit code 0 = all hard checks pass. Exit code 1 = at least one FAIL.
"""
import sys
import re
import json
import argparse

from config_loader import CONFIG
from constants import (
    LINK_BUDGET, META_TITLE_MAX, META_DESC_MIN, META_DESC_MAX, MIN_STAT_YEAR, FAQ_BAND,
)

BRAND = CONFIG["brand_name"]
# Strip a leading "www." PREFIX only. str.lstrip removes a character SET, so the
# old lstrip("www.") mangled any domain starting with w/. (e.g. wine.com).
DOMAIN = re.sub(r"^www\.", "", CONFIG["domain"].lower())
MAX_BRAND = int(CONFIG.get("max_brand_mentions", 1))
COUNTRY_SLUGS = set(CONFIG.get("country_slugs", []))

# ---- rule tables -----------------------------------------------------------

# "try" is anchored to the start of the anchor text (real CTAs open with the verb,
# e.g. "Try it now") so a topic anchor like "why teams try agile frameworks" doesn't
# falsely trip the check.
CTA_ANCHOR_PATTERNS = [
    r"\bexplore\b", r"\bdiscover\b", r"\bget started\b", r"\blearn more\b",
    r"\bview all\b", r"\bcheck out\b", r"^\s*try\b", r"\bclick here\b", r"\bread more\b",
]
_CTA_RE = re.compile("|".join(CTA_ANCHOR_PATTERNS), re.I)

# British spellings -> flag. Word-boundary regexes to cut false positives.
BRITISH_PATTERNS = [
    r"\b\w+ise\b", r"\b\w+isation\b", r"\b\w+ised\b", r"\b\w+ising\b",
    r"\bcolour\b", r"\bbehaviour\b", r"\bfavour\b", r"\borganis\w*\b",
    r"\banalyse\b", r"\banalysed\b", r"\banalysing\b",
    r"\bcentre\b", r"\blicence\b", r"\bdefence\b", r"\bprogramme\b",
    r"\bcatalogue\b", r"\bfulfil\b", r"\bmodelling\b", r"\blabelled\b",
]
_BRITISH_RE = re.compile("|".join(BRITISH_PATTERNS), re.I)

# Words that legitimately end in -ise/-ised/-ising in American English. The broad
# \w+ise pattern would otherwise flag these (advertise, improvise, supervise ...).
_AMERICAN_ISE_BASES = {
    "rise", "wise", "advise", "revise", "surprise", "comprise", "exercise",
    "franchise", "arise", "expertise", "precise", "concise", "promise",
    "premise", "otherwise", "likewise", "raise", "praise", "supervise",
    "devise", "noise", "poise", "cruise", "paradise", "merchandise",
    "compromise", "enterprise", "advertise", "improvise", "despise",
    "disguise", "excise", "incise", "chastise", "reprise", "demise", "guise",
    "clockwise", "crosswise", "lengthwise", "expertise", "excise",
}


def _ise_forms(bases):
    """Base plus its -ed/-ing/-s inflections, so 'supervise' also allows 'supervised'."""
    out = set()
    for b in bases:
        out.add(b)
        out.add(b + "s")
        if b.endswith("e"):
            out.add(b[:-1] + "ed")
            out.add(b[:-1] + "ing")
    return out


BRITISH_ALLOW = _ise_forms(_AMERICAN_ISE_BASES)


def find_british_spellings(text):
    """Return the sorted unique British-spelled words in text (allowlist applied)."""
    brit = []
    for m in _BRITISH_RE.finditer(text):
        w = m.group(0).lower()
        if w not in BRITISH_ALLOW:
            brit.append(w)
    return sorted(set(brit))

# Build a regex that matches <domain>/<country-slug>/ in a URL (from config).
if COUNTRY_SLUGS:
    _COUNTRY_PATTERN = re.compile(
        re.escape(DOMAIN) + r"/(" + "|".join(re.escape(c) for c in sorted(COUNTRY_SLUGS)) + r")(/|$)",
        re.I,
    )
else:
    _COUNTRY_PATTERN = None

# ---- helpers ---------------------------------------------------------------

def strip_tags(html):
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    return re.sub(r"<[^>]+>", " ", html)

def strip_note_blocks(html):
    """Remove every <div class="note" ...>...</div> block, honoring nested <div>s.

    A plain non-greedy regex stops at the FIRST </div>, so a note that wraps a
    table (the changes-summary and publishing boxes both do) is only half removed,
    which inflates the reader word count and can leak note links into the budget.
    This walks div open/close depth to remove the whole block.
    """
    tag = re.compile(r'<(/?)div\b', re.I)
    start = re.compile(r'<div class="note"', re.I)
    out, i = [], 0
    while True:
        m = start.search(html, i)
        if not m:
            out.append(html[i:])
            return "".join(out)
        out.append(html[i:m.start()])
        depth, end = 0, len(html)
        for tm in tag.finditer(html, m.start()):
            depth += 1 if tm.group(1) == "" else -1
            if depth == 0:
                gt = html.find(">", tm.end() - 1)
                end = gt + 1 if gt != -1 else tm.end()
                break
        i = end


def reader_text(html):
    """Visible text with review/publishing notes removed (they are not reader-facing)."""
    return strip_tags(strip_note_blocks(html))

def link_band(words):
    for max_w, i_max, e_max in LINK_BUDGET:
        if words <= max_w:
            return i_max, e_max
    return LINK_BUDGET[-1][1], LINK_BUDGET[-1][2]

def faq_band(words):
    for max_w, lo, hi in FAQ_BAND:
        if words <= max_w:
            return lo, hi
    return FAQ_BAND[-1][1], FAQ_BAND[-1][2]


_HEADING_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.I | re.S)


def section_chunks(html):
    """Split into (level, heading_text, body_html) chunks: body_html is everything
    between one heading and the next (or end of document). Feed it a note-stripped
    reader body. Used by the section self-sufficiency and snippet-length checks."""
    matches = list(_HEADING_RE.finditer(html))
    chunks = []
    for i, m in enumerate(matches):
        level = int(m.group(1))
        heading_text = strip_tags(m.group(2)).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        chunks.append((level, heading_text, html[start:end]))
    return chunks


_DANGLING_OPEN_RE = re.compile(
    r"^\s*(it|this|that|they|these|those|so|then|thus|also|however)\b", re.I)


def dangling_reference_sections(html):
    """H2/H3 sections whose first sentence opens with a bare pronoun/connective
    (It/This/That/They/These/Those/So/Then/Thus/Also/However) - a strong signal the
    section depends on a PRIOR section to make sense, so an AI answer engine
    quoting just this chunk would produce a confusing or wrong answer. Returns the
    flagged heading texts."""
    flagged = []
    for level, heading, body_html in section_chunks(html):
        if level not in (2, 3):
            continue
        body_text = strip_tags(body_html).strip()
        if body_text and _DANGLING_OPEN_RE.match(body_text):
            flagged.append(heading)
    return flagged


def long_paragraphs(html, max_words=120):
    """Reader-facing <p> blocks exceeding max_words - a chunk-friendliness signal
    for GEO retrieval, which typically slices content into ~200-500 token pieces;
    an extremely long unbroken paragraph risks truncation mid-thought. Returns a
    list of (word_count, preview) for each flagged paragraph, feed it reader_html."""
    flagged = []
    for p in re.findall(r"<p[\s>][\s\S]*?</p>", html, re.I):
        words = strip_tags(p).split()
        if len(words) > max_words:
            flagged.append((len(words), " ".join(words[:12]) + "..."))
    return flagged


_QUESTION_HEADING_RE = re.compile(
    r"^(what|how|why|when|where|who|which|is|are|can|does|do|should)\b", re.I)


def long_question_answers(html, max_words=70):
    """Question-phrased H2/H3 sections (What is.../How to.../Why does...) whose
    first paragraph runs well past featured-snippet length (Google's AI Overview/
    snippet sweet spot is roughly 40-60 words). Feed it a note-stripped reader
    body. Returns [(heading, word_count), ...] for sections over max_words."""
    flagged = []
    for level, heading, body_html in section_chunks(html):
        if level not in (2, 3):
            continue
        is_question = heading.rstrip().endswith("?") or _QUESTION_HEADING_RE.match(heading.strip())
        if not is_question:
            continue
        first_p = re.search(r"<p[\s>][\s\S]*?</p>", body_html, re.I)
        para_text = strip_tags(first_p.group(0)) if first_p else strip_tags(body_html)
        words = para_text.split()
        if len(words) > max_words:
            flagged.append((heading, len(words)))
    return flagged


_ACRONYM_DEF_RE = re.compile(r"[A-Za-z][\w&/-]*(?:\s[A-Za-z][\w&/-]*){0,4}\s*\(([A-Z]{2,6}s?)\)")
_BARE_ACRONYM_RE = re.compile(r"\b([A-Z]{2,6}s?)\b")


def acronym_definitions(text):
    """Acronyms defined via an 'expansion phrase (ACRONYM)' pattern in text."""
    return set(_ACRONYM_DEF_RE.findall(text))


def undefined_acronym_reuse(html):
    """H2/H3 sections that use an acronym defined via '(ACRONYM)' in an EARLIER
    section but do not redefine it themselves - a section quoted in isolation by
    an AI answer engine would show an undefined acronym. Deliberately narrow (only
    acronyms the page itself chose to define this way) to avoid flagging common,
    no-longer-jargon acronyms (AI, ROI, FAQ) that were never defined via this
    pattern anywhere. Returns [(heading, acronym), ...]."""
    seen_defined = set()
    flagged = []
    for level, heading, body_html in section_chunks(html):
        if level not in (2, 3):
            continue
        body_text = strip_tags(body_html)
        local_defs = acronym_definitions(body_text)
        for acr in set(_BARE_ACRONYM_RE.findall(body_text)):
            if acr not in local_defs and acr in seen_defined:
                flagged.append((heading, acr))
        seen_defined |= local_defs
    return flagged


def faq_answer_fragments(html, min_words=8):
    """FAQ answers that read as sentence fragments rather than complete sentences -
    a voice assistant reads the answer aloud verbatim, so a fragment sounds broken.
    Flags an answer under min_words or missing sentence-ending punctuation.
    Returns the flagged answer texts (truncated for display by the caller)."""
    answers = re.findall(r'itemprop="text"[^>]*>([\s\S]*?)</p>', html, re.I)
    flagged = []
    for a in answers:
        t = strip_tags(a).strip()
        if t and (len(t.split()) < min_words or not t.endswith((".", "!", "?", '"', "”"))):
            flagged.append(t)
    return flagged


def _syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)

def flesch_reading_ease(text):
    """Rough Flesch Reading Ease. 60+ is the target (plain, readable prose)."""
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[A-Za-z]+", text)
    if not sentences or not words:
        return None
    syl = sum(_syllables(w) for w in words)
    wps = len(words) / len(sentences)
    spw = syl / len(words)
    return round(206.835 - 1.015 * wps - 84.6 * spw, 1)

def extract_jsonld_blocks(html):
    """Return the raw text of every <script type="application/ld+json"> block."""
    return re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>',
        html, re.I,
    )


def invalid_jsonld_blocks(html):
    """Return a list of (index, error) for JSON-LD blocks that do not parse as JSON."""
    bad = []
    for i, block in enumerate(extract_jsonld_blocks(html), 1):
        try:
            json.loads(block.strip())
        except ValueError as e:
            bad.append((i, str(e).split("\n")[0]))
    return bad


def heading_levels(html):
    """Ordered list of heading levels (1-6) in the document, comments stripped."""
    html = re.sub(r"<!--[\s\S]*?-->", " ", html)
    return [int(m.group(1)) for m in re.finditer(r"<h([1-6])[\s>]", html, re.I)]


def heading_hierarchy_errors(levels):
    """Report a missing/duplicate H1 and any skipped level (e.g. H2 jumping to H4)."""
    errors = []
    n_h1 = levels.count(1)
    if n_h1 != 1:
        errors.append(f"expected exactly one H1, found {n_h1}")
    prev = None
    for lv in levels:
        if prev is not None and lv > prev + 1:
            errors.append(f"skipped level: H{prev} to H{lv}")
        prev = lv
    return errors


_GENERIC_IMG_RE = re.compile(
    r"(image\d+|img[_-]?\d+|dsc[_-]?\d+|screenshot|untitled|photo\d+|unnamed)\.", re.I)


def image_issues(html):
    """Report <img> tags missing/empty alt text or using a generic filename."""
    html = re.sub(r"<!--[\s\S]*?-->", " ", html)
    issues = []
    for tag in re.findall(r"<img\s[^>]*>", html, re.I):
        alt = re.search(r'\balt="([^"]*)"', tag, re.I)
        if not alt or not alt.group(1).strip():
            issues.append("missing/empty alt")
        src = re.search(r'\bsrc="([^"]*)"', tag, re.I)
        if src and _GENERIC_IMG_RE.search(src.group(1)):
            issues.append("generic filename: " + src.group(1))
    return issues


def keyword_placement(html, text, h1_text, meta_title, keyword):
    """Where the primary keyword lands: title/H1/first-100-words/conclusion + total count."""
    kw = keyword.lower().strip()
    tl = text.lower()
    first100 = " ".join(text.split()[:100]).lower()
    concl_m = re.search(r"<h2[^>]*>\s*conclusion[\s\S]*", html, re.I)
    concl_text = strip_tags(concl_m.group(0)).lower() if concl_m else None
    return {
        "in_title": kw in (meta_title or "").lower(),
        "in_h1": kw in (h1_text or "").lower(),
        "in_first_100": kw in first100,
        "in_conclusion": (kw in concl_text) if concl_text is not None else None,
        "count": tl.count(kw),
    }


_STAT_SIGNAL_RE = re.compile(
    r"%|\bpercent\b|\bstud(y|ies)\b|\bsurvey\b|\breport\b|\bdata\b|\bstatistics?\b|\bgrowth\b|\bmarket\b",
    re.I)


def stale_stat_years(text, min_year=MIN_STAT_YEAR):
    """Years before min_year that sit next to a statistic signal (a %, 'study', etc.).

    Historical mentions ("founded in 1998") have no adjacent stat signal, so they are
    not flagged; a "2021 study found 45%" is. Returns sorted unique flagged years.
    """
    flagged = set()
    for m in re.finditer(r"\b(19\d\d|20\d\d)\b", text):
        year = int(m.group(1))
        if year >= min_year:
            continue
        window = text[max(0, m.start() - 45): m.end() + 45]
        if _STAT_SIGNAL_RE.search(window):
            flagged.add(year)
    return sorted(flagged)


def repeated_percent_stats(text, min_repeats=3):
    """Exact percentage values (e.g. '40%') repeated min_repeats+ times in the reader
    text. Reusing the identical figure across sections is a padding/repetition signal
    (Rule 14: no repeats) that the mechanical FAQ/JSON-LD count checks cannot catch,
    since it is about content variety, not structure. Returns {value: count}."""
    counts = {}
    for m in re.finditer(r"\b\d{1,3}(?:\.\d+)?%", text):
        counts[m.group(0)] = counts.get(m.group(0), 0) + 1
    return {v: c for v, c in counts.items() if c >= min_repeats}


def has_freshness_signal(html, text, min_year=MIN_STAT_YEAR):
    """True if the page shows a current-year freshness date: a JSON-LD dateModified/
    datePublished >= min_year, or visible 'updated/reviewed ... 20YY' >= min_year."""
    for m in re.finditer(r'"date(?:Modified|Published)"\s*:\s*"(\d{4})', html):
        if int(m.group(1)) >= min_year:
            return True
    for m in re.finditer(r"(updated|reviewed|refreshed)[^.<]{0,30}?\b(20\d\d)\b", text, re.I):
        if int(m.group(2)) >= min_year:
            return True
    return False


def schema_completeness(html):
    """Report incomplete typed JSON-LD blocks and which recommended types are absent.

    Returns (missing_fields, absent_types): missing_fields is a list of strings for a
    present Article/BlogPosting/HowTo that lacks required fields; absent_types lists
    recommended schema (Article, BreadcrumbList) not present at all (informational).
    Parses each block as JSON (invalid blocks are already caught separately by
    invalid_jsonld_blocks and are just skipped here) rather than substring-matching
    the concatenated text, so nested fields (author.jobTitle, HowTo.step[].name) can
    actually be checked, not just top-level key presence.
    """
    missing = []
    has_article = has_breadcrumb = False

    for block in extract_jsonld_blocks(html):
        try:
            data = json.loads(block.strip())
        except ValueError:
            continue
        t = data.get("@type") if isinstance(data, dict) else None

        if t in ("Article", "BlogPosting"):
            has_article = True
            for field in ("headline", "author", "datePublished", "dateModified"):
                if field not in data:
                    missing.append(field)

        elif t == "BreadcrumbList":
            has_breadcrumb = True

        elif t == "HowTo":
            if "name" not in data:
                missing.append("HowTo.name")
            steps = data.get("step") or []
            if not steps:
                missing.append("HowTo.step (no steps listed)")
            for i, s in enumerate(steps, 1):
                if not (isinstance(s, dict) and s.get("name") and s.get("text")):
                    missing.append(f"HowTo.step[{i}] missing name/text")

    absent = []
    if not has_article:
        absent.append("Article/BlogPosting")
    if not has_breadcrumb:
        absent.append("BreadcrumbList")
    return missing, absent


def author_credential_gap(html):
    """True if an Article/BlogPosting's author is a Person node lacking jobTitle
    or description - a weak E-E-A-T signal. Soft/informational, not a hard schema
    requirement: a bare-string author (just a name) has no structured field to add
    credentials to, so it is not flagged here."""
    for block in extract_jsonld_blocks(html):
        try:
            data = json.loads(block.strip())
        except ValueError:
            continue
        if not isinstance(data, dict) or data.get("@type") not in ("Article", "BlogPosting"):
            continue
        author = data.get("author")
        if isinstance(author, dict) and not (author.get("jobTitle") or author.get("description")):
            return True
    return False

# ---- checks ----------------------------------------------------------------

def run(path, forced_words=None, is_new=False, keyword=None):
    with open(path, encoding="utf-8") as f:
        html = f.read()

    results = []   # (ok, label, detail)
    info = []      # (label, detail) informational, not pass/fail
    def check(ok, label, detail=""):
        results.append((bool(ok), label, detail))

    text = reader_text(html)
    # The link budget is governed by the word count the tool computes itself, so a
    # too-high --words can no longer unlock a larger link budget than the copy earns.
    # --words stays advisory: it is reported, and a large divergence is flagged.
    computed_words = len(text.split())
    words = computed_words
    if forced_words:
        diff = abs(forced_words - computed_words)
        if diff > max(150, 0.15 * computed_words):
            info.append(("Word count divergence",
                         f"--words={forced_words} vs computed {computed_words}; "
                         f"link band uses computed. Recheck the passed count."))

    # 1-3. Dashes
    em = html.count("—")
    en = html.count("–")
    dbl = len(re.findall(r"(?<=\w)--(?=\s)|(?<=\s)--(?=\w)", html))
    check(em == 0, "Em dashes = 0", f"found {em}")
    check(en == 0, "En dashes = 0", f"found {en}")
    check(dbl == 0, "Double-hyphen breaks = 0", f"found {dbl}")

    # 4. Brand mentions in reader body (0..MAX_BRAND, conclusion only)
    brand_re = re.compile(re.escape(BRAND), re.I)
    inv = len(brand_re.findall(text))
    check(inv <= MAX_BRAND, f"Brand in body <= {MAX_BRAND}", f"found {inv} (notes excluded)")

    # 5. Links + budget
    reader_html = strip_note_blocks(html)
    reader_hrefs = re.findall(r'<a\s[^>]*href="([^"]+)"[^>]*>', reader_html, re.I)
    internal = [h for h in reader_hrefs if DOMAIN in h.lower() or h.startswith("/")]
    external = [h for h in reader_hrefs if h.startswith("http") and DOMAIN not in h.lower()]
    i_max, e_max = link_band(words)
    check(len(internal) <= i_max, f"Internal links <= {i_max} (~{words} words)", f"found {len(internal)}")
    check(len(external) <= e_max, f"External hyperlinks <= {e_max}", f"found {len(external)}")

    # 6. Max 1 link per <p>
    over = 0
    for p in re.findall(r"<p[\s>][\s\S]*?</p>", html, re.I):
        if len(re.findall(r"<a\s", p, re.I)) > 1:
            over += 1
    check(over == 0, "Max 1 link per paragraph", f"{over} paragraphs over")

    # 7. CTA anchor text
    anchors = re.findall(r"<a\s[^>]*>([\s\S]*?)</a>", reader_html, re.I)
    cta_hits = [strip_tags(a).strip() for a in anchors if _CTA_RE.search(strip_tags(a))]
    check(not cta_hits, "No CTA-style anchor text", "; ".join(cta_hits[:5]))

    # 8. British spellings
    brit = find_british_spellings(text)
    check(not brit, "American English only", ", ".join(brit[:8]))

    # 9. Meta title length
    mt = re.search(r"Meta title\s*\((\d+)\s*/\s*\d+\)\s*:</strong>\s*([^<]+)", html)
    if mt:
        title_txt = mt.group(2).strip()
        check(len(title_txt) <= META_TITLE_MAX, f"Meta title <= {META_TITLE_MAX} chars",
              f"{len(title_txt)} chars: {title_txt}")
    else:
        check(False, "Meta title field present", "not found in publishing-fields box")

    # 10. Meta description length
    md = re.search(r"Meta description\s*\((\d+)\s*/\s*\d+\)\s*:</strong>\s*([^<]+)", html)
    if md:
        desc = md.group(2).strip()
        check(META_DESC_MIN <= len(desc) <= META_DESC_MAX,
              f"Meta description {META_DESC_MIN}-{META_DESC_MAX} chars", f"{len(desc)} chars")
    else:
        check(False, "Meta description field present", "not found in publishing-fields box")

    # 11. H1 present
    h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
    check(bool(h1), "H1 present", strip_tags(h1.group(1)).strip() if h1 else "missing")

    # 12. AIO opening paragraph
    h1_match = re.search(r"</h1>\s*(?:<[^p][^>]*>[\s\S]*?)*<p[^>]*>([\s\S]*?)</p>", html, re.I)
    if h1_match:
        first_p = strip_tags(h1_match.group(1)).strip()
        check(len(first_p.split()) >= 30, "AIO opening paragraph (30+ words)", f"{len(first_p.split())} words")
    else:
        check(False, "AIO opening paragraph present", "no <p> found after <h1>")

    # 13. Review markers (optimize mode only). New pages ship clean, no diff markers.
    if is_new:
        # Match the real markup (class="remove-block" / class="new-block"), not a
        # ".remove-block" CSS-selector string that never appears in the HTML body.
        has_remove = bool(re.search(r'class="[^"]*\bremove-block\b', html))
        has_new = bool(re.search(r'class="[^"]*\bnew-block\b', html))
        check(not has_remove, "New page: no leftover removal markers", "found remove-block")
        check(not has_new, "New page: no leftover addition markers", "found new-block")
    else:
        check(bool(re.search(r'class="[^"]*\bnew-block\b', html)), "new-block used for additions")
        # 13b. End "changes summary" table documenting what was done
        check("changes-summary" in html, "Changes summary table present",
              'add a table with class="changes-summary" listing section / action / reason')

    # 14. External links have rel=nofollow + target=_blank
    ext_tags = [t for t in re.findall(r"<a\s[^>]*>", reader_html, re.I)
                if re.search(r'href="https?://', t) and DOMAIN not in t.lower()]
    bad_ext = [t for t in ext_tags if "nofollow" not in t.lower() or "_blank" not in t.lower()]
    check(not bad_ext, "External links rel=nofollow target=_blank", f"{len(bad_ext)} missing attrs")

    # 15. FAQ HTML count == JSON-LD count (if JSON-LD present)
    faq_html = len(re.findall(r'itemprop="name"', html))
    ld = re.search(r'"@type"\s*:\s*"FAQPage"', html)
    if ld:
        ld_q = len(re.findall(r'"@type"\s*:\s*"Question"', html))
        check(faq_html == ld_q and faq_html > 0, "FAQ HTML == JSON-LD count", f"html={faq_html} jsonld={ld_q}")
    else:
        check(faq_html > 0, "FAQ present (microdata)", f"{faq_html} questions; no JSON-LD script block")

    # 15a. FAQ count within the word-count band (Rule 11; QUALITY-RULES.md FAQ count bands)
    faq_lo, faq_hi = faq_band(words)
    check(faq_lo <= faq_html <= faq_hi, f"FAQ count in {faq_lo}-{faq_hi} band (~{words} words)",
          f"found {faq_html}")

    # 15b. Every JSON-LD block parses as valid JSON
    bad_ld = invalid_jsonld_blocks(html)
    check(not bad_ld, "JSON-LD blocks parse as valid JSON",
          "; ".join(f"block {i}: {err}" for i, err in bad_ld[:3]))

    # 15c. Heading hierarchy: one H1, no skipped levels (AI parse map)
    h_errors = heading_hierarchy_errors(heading_levels(html))
    check(not h_errors, "Heading hierarchy (one H1, no skipped levels)", "; ".join(h_errors[:4]))

    # 15d. Image SEO: every <img> has alt text and a non-generic filename
    img_probs = image_issues(html)
    check(not img_probs, "Images have descriptive alt + filename", "; ".join(img_probs[:4]))

    # 15e. Primary-keyword placement (only when --keyword is supplied; Rule 2)
    if keyword:
        h1_text = strip_tags(h1.group(1)).strip() if h1 else ""
        title_txt = mt.group(2).strip() if mt else ""
        kp = keyword_placement(html, text, h1_text, title_txt, keyword)
        check(kp["in_h1"], f'Primary keyword "{keyword}" in H1')
        check(kp["in_first_100"], f'Primary keyword in first 100 words')
        check(1 <= kp["count"] <= 6, "Primary keyword not stuffed (1-6 uses)", f'{kp["count"]} uses')
        if kp["in_conclusion"] is None:
            info.append(("Primary keyword in conclusion", "no Conclusion H2 found to check"))
        else:
            check(kp["in_conclusion"], "Primary keyword in conclusion")
        info.append(("Primary keyword in meta title", "yes" if kp["in_title"] else "NO (add it)"))

    # 15f. Stale stats (Rule 12): pre-2024 years next to a statistic signal
    stale = stale_stat_years(text)
    check(not stale, f"No pre-{MIN_STAT_YEAR} stats", "years near stats: " + ", ".join(map(str, stale)))

    # 15g. Freshness: a current-year updated/modified date is present (top GEO lever)
    check(has_freshness_signal(html, text),
          f"Freshness date present (>= {MIN_STAT_YEAR})",
          'add a visible "Last updated: <Month> <year>" or JSON-LD dateModified')

    # 15h. Schema completeness: a present Article must be complete; recommend the set
    missing_fields, absent_types = schema_completeness(html)
    check(not missing_fields, "Article schema complete (if present)",
          "missing: " + ", ".join(missing_fields))
    if absent_types:
        info.append(("Recommended schema absent", ", ".join(absent_types) + " (add when applicable)"))
    if author_credential_gap(html):
        info.append(("Author schema missing credentials",
                      "add jobTitle or description to the author Person node (E-E-A-T)"))

    # 16. Rough tag balance (ignore tags inside HTML comments, e.g. template examples)
    html_no_comments = re.sub(r"<!--[\s\S]*?-->", " ", html)
    for tag in ["div", "p", "table", "section"]:
        o = len(re.findall(rf"<{tag}[\s>]", html_no_comments, re.I))
        c = len(re.findall(rf"</{tag}>", html_no_comments, re.I))
        check(o == c, f"<{tag}> balanced", f"open={o} close={c}")

    # 17. No country/city page links
    geo_links = []
    if _COUNTRY_PATTERN:
        for href in reader_hrefs:
            m = _COUNTRY_PATTERN.search(href)
            if m:
                geo_links.append(f"{m.group(1)}: {href}")
    check(not geo_links, "No country/city page links", "; ".join(geo_links[:5]) if geo_links else "")

    # Informational: readability (manual judgment, not a hard gate)
    fre = flesch_reading_ease(text)
    if fre is not None:
        verdict = "good" if fre >= 60 else "ok" if fre >= 50 else "hard to read, simplify"
        info.append(("Flesch reading ease", f"{fre} ({verdict}; target 60+)"))

    # Informational: the same exact stat reused 3+ times reads as padding (Rule 14)
    repeats = repeated_percent_stats(text)
    if repeats:
        detail = ", ".join(f"{v} x{c}" for v, c in sorted(repeats.items(), key=lambda x: -x[1]))
        info.append(("Repeated stat", f"{detail} - vary the supporting point or drop duplicates"))

    # Informational: section self-sufficiency for AI extraction (AI answer engines
    # usually quote a single H2/H3 chunk, not the whole page)
    dangling = dangling_reference_sections(reader_html)
    if dangling:
        info.append(("Section may depend on prior context",
                      "; ".join(dangling[:5]) + " - opens on a bare pronoun, restate the subject"))

    long_paras = long_paragraphs(reader_html)
    if long_paras:
        detail = "; ".join(f"{n} words (\"{prev}\")" for n, prev in long_paras[:3])
        info.append(("Long paragraph (chunk-friendliness)", detail))

    long_qa = long_question_answers(reader_html)
    if long_qa:
        detail = "; ".join(f'"{h}" ({n} words)' for h, n in long_qa[:3])
        info.append(("Question-heading answer over snippet length (~60w target)", detail))

    frags = faq_answer_fragments(html)
    if frags:
        detail = "; ".join(f'"{f[:60]}..."' if len(f) > 60 else f'"{f}"' for f in frags[:3])
        info.append(("FAQ answer reads as a fragment (voice-readability)", detail))

    reused = undefined_acronym_reuse(reader_html)
    if reused:
        detail = "; ".join(f'"{h}" reuses {a}' for h, a in reused[:5])
        info.append(("Acronym reused without local redefinition", detail))

    # ---- report ----
    mode = "NEW page" if is_new else "OPTIMIZE existing"
    print(f"\nQA REPORT  -  {path}")
    print(f"mode: {mode}  |  brand: {BRAND}  |  domain: {DOMAIN}")
    print(f"reader word count: {words}  |  link band: internal<={i_max} external<={e_max}\n")
    passed = 0
    for ok, label, detail in results:
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {label}"
        if detail and not ok:
            line += f"   ({detail})"
        print(line)
        passed += ok
    for label, detail in info:
        print(f"  [INFO] {label}: {detail}")
    fails = [r for r in results if not r[0]]
    print(f"\n{passed}/{len(results)} checks passed.")
    if fails:
        print("FAILURES:")
        for _, label, detail in fails:
            print(f"  - {label}: {detail}")
    return 0 if not fails else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--words", type=int, default=None, help="reader-facing word count for link budget")
    ap.add_argument("--new", action="store_true",
                    help="new-blog mode: expect clean HTML (no diff markers or changes-summary)")
    ap.add_argument("--keyword", default=None,
                    help="primary keyword: check placement in title/H1/first-100/conclusion (Rule 2)")
    a = ap.parse_args()
    sys.exit(run(a.file, a.words, a.new, a.keyword))
