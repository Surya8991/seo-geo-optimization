#!/usr/bin/env python3
"""
Rule 6 helper: before adding a new H2 (or FAQ), check whether another page or blog
post already owns that subtopic, so you link to it instead of writing a competing
section.

Usage:
    python optimizer/cannibal.py "training roi"
    python optimizer/cannibal.py "leadership styles" --exclude product-certification

Searches pages (from data/scorecard.json "pages"), blog pages (from data/audit.json
"blog_pages"), AND the content ledger (new sections this pipeline already produced).
Results are labelled [PAGE], [BLOG], or [LEDGER] so you know which type matched. A
[LEDGER] hit means a past build already wrote that section: link to it, do not repeat.
"""
import json
import os
import re
import sys
import argparse

try:
    from ledger import search as ledger_search
except ImportError:
    ledger_search = None

try:
    from constants import STOP_WORDS as STOP
except ImportError:
    from optimizer.constants import STOP_WORDS as STOP

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORECARD = os.path.join(BASE, "data", "scorecard.json")
AUDIT = os.path.join(BASE, "data", "audit.json")


def tokens(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2]


def main(phrase, exclude):
    scored = []
    q_words = set(tokens(phrase))
    phrase_l = phrase.lower().strip()

    # --- Pages (full scorecard data) ---
    if os.path.exists(SCORECARD):
        pages = json.load(open(SCORECARD, encoding="utf-8")).get("pages", [])
        for p in pages:
            hay = (p.get("title", "") + " " + p.get("url", "") + " " + p.get("slug", "")).lower()
            if exclude and exclude.lower() in hay:
                continue
            score = 0
            if phrase_l in hay:
                score += 100
            overlap = q_words & set(tokens(hay))
            score += len(overlap) * 10
            if score:
                scored.append((score, len(overlap), "PAGE", p))
    else:
        print(f"WARNING: scorecard not found: {SCORECARD}")

    # --- Blog pages (may be strings or dicts) ---
    if os.path.exists(AUDIT):
        audit_data = json.load(open(AUDIT, encoding="utf-8"))
        blog_pages = audit_data.get("blog_pages", [])
        for b in blog_pages:
            if isinstance(b, str):
                slug = b
                title = slug.replace("blog/", "").replace("-", " ")
                b = {"slug": slug, "title": title}
            hay = (b.get("title", "") + " " + b.get("slug", "")).lower()
            if exclude and exclude.lower() in hay:
                continue
            score = 0
            if phrase_l in hay:
                score += 100
            overlap = q_words & set(tokens(hay))
            score += len(overlap) * 10
            if score:
                scored.append((score, len(overlap), "BLOG", b))

    # --- Content ledger (new sections already produced by this pipeline) ---
    if ledger_search is not None:
        for score, e in ledger_search(phrase):
            if exclude and exclude.lower() in e.get("page_slug", "").lower():
                continue
            scored.append((score, 0, "LEDGER", e))

    scored.sort(key=lambda x: (-x[0], -x[1]))

    if not scored:
        print(f'No existing page, blog, or ledger entry matches "{phrase}". Safe to write a new section.')
        return 0

    print(f'\nExisting pages overlapping "{phrase}" (strongest first):\n')
    for score, ov, page_type, p in scored[:15]:
        flag = "  <-- STRONG OVERLAP, link instead of writing" if score >= 100 else ""
        if page_type == "PAGE":
            url = p.get("url", p.get("slug", "?"))
            cat = p.get("category", "?")
            clicks = p.get("clicks_16m", "?")
            pos = p.get("position", "?")
            print(f'  [{score:>3}] [{page_type}] {cat:<22} {url}')
            print(f'        "{p.get("title","")}"  (clicks16m={clicks}, pos={pos}){flag}')
        elif page_type == "LEDGER":
            lflag = "  <-- ALREADY WRITTEN by a past build, link to it, do not repeat" if score >= 100 else flag
            print(f'  [{score:>3}] [{page_type}] {p.get("page_slug","?")}')
            print(f'        "{p.get("section","")}"{lflag}')
        else:
            slug = p.get("slug", "?")
            title = p.get("title", "")
            print(f'  [{score:>3}] [{page_type}] {slug}')
            print(f'        "{title}"{flag}')

    print("\nRule 6: if a strong overlap exists, add a 1-2 sentence mention + internal link,")
    print("or skip the section. Only write a full new section when nothing here covers it.")
    print("A [LEDGER] hit means a past build already wrote it: reuse via link, never duplicate.\n")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phrase", help="proposed section title or subtopic")
    ap.add_argument("--exclude", default=None, help="slug/url fragment of the page being optimized")
    a = ap.parse_args()
    sys.exit(main(a.phrase, a.exclude))
