#!/usr/bin/env python3
"""
Inbound internal-link finder (Checklist #29: min 5 internal links FROM other pages
TO this one). cannibal.py guards against duplicate topics; this does the opposite,
surfacing existing pages that SHOULD link to the page you are optimizing, so you can
add contextual inbound links from them.

It ranks existing pages by topical overlap with the target's title + primary keyword,
skips the target itself and any country/city pages (config country_slugs), and prints
the strongest candidates as inbound-link opportunities.

Usage:
    python optimizer/interlink.py info/product-certification
    python optimizer/interlink.py "agile scrum"
"""
import json
import os
import re
import sys

try:
    from constants import STOP_WORDS as STOP
except ImportError:
    from optimizer.constants import STOP_WORDS as STOP
try:
    from config_loader import CONFIG
except ImportError:
    from optimizer.config_loader import CONFIG

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORECARD = os.path.join(BASE, "data", "scorecard.json")
AUDIT = os.path.join(BASE, "data", "audit.json")


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", str(s).lower()) if w not in STOP and len(w) > 2}


def slug_tail(slug):
    return re.sub(r"/+$", "", str(slug)).rsplit("/", 1)[-1].lower()


def is_country_page(slug_or_url, country_slugs):
    tail = slug_tail(slug_or_url)
    return tail in {c.lower() for c in country_slugs}


def rank_inbound(target_tokens, pages, exclude_tail, country_slugs):
    """Rank source pages by token overlap with the target; skip target + geo pages."""
    scored = []
    for p in pages:
        ident = p.get("slug") or p.get("url", "")
        if slug_tail(ident) == exclude_tail:
            continue
        if is_country_page(ident, country_slugs):
            continue
        overlap = target_tokens & tokens(p.get("title", "") + " " + ident)
        if overlap:
            scored.append((len(overlap), sorted(overlap), p))
    scored.sort(key=lambda x: (-x[0], x[2].get("slug", "")))
    return scored


def _load(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def resolve_target_tokens(target, pages, audit_rows):
    """Tokens for the target: title + primary_keyword if the target is a known page,
    otherwise just the raw phrase. Returns (tokens, exclude_tail, label)."""
    frag = target.lower().strip().rstrip("/")
    for r in audit_rows:
        hay = " ".join(str(r.get(k, "")) for k in ("url", "slug", "title")).lower()
        if frag in hay:
            toks = tokens(r.get("title", "") + " " + r.get("primary_keyword", ""))
            return toks, slug_tail(r.get("slug") or r.get("url", "")), r.get("title") or frag
    for p in pages:
        hay = " ".join(str(p.get(k, "")) for k in ("url", "slug", "title")).lower()
        if frag in hay:
            return tokens(p.get("title", "")), slug_tail(p.get("slug") or p.get("url", "")), p.get("title") or frag
    return tokens(target), None, target


def main(target):
    if not os.path.exists(SCORECARD):
        print(f"ERROR: {SCORECARD} not found. Run build_scorecard.py or copy scorecard.example.json.")
        return 1
    pages = _load(SCORECARD, {}).get("pages", [])
    audit_rows = _load(AUDIT, {}).get("audit_rows", [])
    country_slugs = CONFIG.get("country_slugs", [])

    target_tokens, exclude_tail, label = resolve_target_tokens(target, pages, audit_rows)
    if not target_tokens:
        print(f"Could not derive topic tokens for '{target}'.")
        return 1

    ranked = rank_inbound(target_tokens, pages, exclude_tail, country_slugs)
    print(f'\nInbound-link opportunities for "{label}" (topic: {", ".join(sorted(target_tokens))}):\n')
    if not ranked:
        print("  No topically related source pages found.")
        return 0
    for score, shared, p in ranked[:15]:
        print(f'  [{score:>2}] {p.get("category","?"):<22} {p.get("slug") or p.get("url")}')
        print(f'        "{p.get("title","")}"  (shared: {", ".join(shared)})')
    print("\nAdd a contextual link FROM each of these TO the target page, with descriptive")
    print("anchor text naming the target topic (Rule 4: no CTA anchors). Aim for 5+ inbound.\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
