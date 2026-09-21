#!/usr/bin/env python3
"""
Content ledger: a forward-guard so a new section written for one page is not written
again, near-verbatim, on a future page. cannibal.py checks EXISTING published pages;
this ledger records the NEW sections and unique angles this pipeline has produced, so
the next page can see "already covered on page X" before duplicating it.

Usage:
    # record new sections after a build (Step 8)
    python optimizer/ledger.py add <page-slug> --section "How to measure training ROI" \
        --angle "formula + worked example" --asset "ROI calculator table"

    # list everything, or one page's entries
    python optimizer/ledger.py list
    python optimizer/ledger.py list <page-slug>

    # search the ledger for a subtopic (cannibal.py calls this internally)
    python optimizer/ledger.py search "training roi"

Stored at data/content_ledger.json.
"""
import argparse
import json
import os
import re
import sys
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(BASE, "data", "content_ledger.json")

STOP = {"the", "a", "an", "of", "for", "to", "in", "and", "or", "how", "what",
        "why", "with", "your", "you", "is", "are", "on", "best", "top", "guide"}


def _tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def load():
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def save(data):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add(slug, section, angle, asset):
    data = load()
    data["entries"].append({
        "page_slug": slug,
        "section": section,
        "angle": angle or "",
        "unique_asset": asset or "",
        "date": date.today().isoformat(),
    })
    save(data)
    print(f"Ledger updated: '{section}' recorded for {slug}.")
    return 0


def list_entries(slug=None):
    data = load()
    rows = [e for e in data["entries"] if not slug or slug.lower() in e["page_slug"].lower()]
    if not rows:
        print("Ledger is empty." if not slug else f"No ledger entries for '{slug}'.")
        return 0
    for e in rows:
        extra = " | ".join(x for x in [e.get("angle"), e.get("unique_asset")] if x)
        print(f'  [{e["date"]}] {e["page_slug"]}: "{e["section"]}"' + (f"  ({extra})" if extra else ""))
    return 0


def search(phrase):
    """Return matching ledger entries (also used by cannibal.py)."""
    data = load()
    q = _tokens(phrase)
    p = phrase.lower().strip()
    hits = []
    for e in data["entries"]:
        hay = (e.get("section", "") + " " + e.get("angle", "")).lower()
        score = (100 if p in hay else 0) + len(q & _tokens(hay)) * 10
        if score:
            hits.append((score, e))
    hits.sort(key=lambda x: -x[0])
    return hits


def _cli_search(phrase):
    hits = search(phrase)
    if not hits:
        print(f'Nothing in the content ledger matches "{phrase}". No prior page claimed it.')
        return 0
    print(f'\nContent ledger overlaps for "{phrase}" (strongest first):\n')
    for score, e in hits[:15]:
        flag = "  <-- ALREADY WRITTEN, do not repeat; link to it" if score >= 100 else ""
        print(f'  [{score:>3}] {e["page_slug"]}: "{e["section"]}"{flag}')
    print()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("slug")
    a.add_argument("--section", required=True)
    a.add_argument("--angle", default="")
    a.add_argument("--asset", default="")

    l = sub.add_parser("list")
    l.add_argument("slug", nargs="?", default=None)

    s = sub.add_parser("search")
    s.add_argument("phrase")

    args = ap.parse_args()
    if args.cmd == "add":
        sys.exit(add(args.slug, args.section, args.angle, args.asset))
    if args.cmd == "list":
        sys.exit(list_entries(args.slug))
    if args.cmd == "search":
        sys.exit(_cli_search(args.phrase))
