#!/usr/bin/env python3
"""
Striking-distance report: pages ranking just off page 1 (avg position 8-20) with real
impressions. These convert to page-1 rankings far more cheaply than writing new pages,
so they are the highest-ROI optimization targets.

Usage:
    python optimizer/striking.py                 # default band 8-20, min 100 impressions
    python optimizer/striking.py 5 20 500        # position 5-20, min 500 impressions
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORECARD = os.path.join(BASE, "data", "scorecard.json")


def striking_pages(pages, lo=8.0, hi=20.0, min_impressions=100):
    """Pages with lo <= avg position <= hi and impressions >= threshold, best first
    (most impressions), since those have the most upside from a small position gain."""
    out = []
    for p in pages:
        pos = p.get("position", 0) or 0
        imp = p.get("impressions", 0) or 0
        if lo <= pos <= hi and imp >= min_impressions:
            out.append(p)
    return sorted(out, key=lambda p: p.get("impressions", 0), reverse=True)


def main(lo, hi, min_imp):
    if not os.path.exists(SCORECARD):
        print(f"ERROR: {SCORECARD} not found. Run build_scorecard.py or copy scorecard.example.json.")
        return 1
    pages = json.load(open(SCORECARD, encoding="utf-8")).get("pages", [])
    hits = striking_pages(pages, lo, hi, min_imp)
    print(f"\nStriking-distance pages (position {lo}-{hi}, impressions >= {min_imp:,}):")
    print(f"{len(hits)} of {len(pages)} pages. Highest upside first:\n")
    for p in hits:
        print(f"  pos {p.get('position'):>5}  imp {p.get('impressions', 0):>9,}  "
              f"CTR {p.get('ctr', 0):>5}%  {p.get('slug') or p.get('url')}")
        if p.get("title"):
            print(f'        "{p["title"]}"  ({p.get("category","?")})')
    print()
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    lo = float(args[0]) if len(args) > 0 else 8.0
    hi = float(args[1]) if len(args) > 1 else 20.0
    min_imp = int(args[2]) if len(args) > 2 else 100
    sys.exit(main(lo, hi, min_imp))
