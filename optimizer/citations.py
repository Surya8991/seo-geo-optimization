#!/usr/bin/env python3
"""
Citation ledger: record every external stat cited across pages, with its source
and year, so staleness can be caught PROACTIVELY (a stat approaching
MIN_STAT_YEAR's cutoff, not just one that already crossed it) and so two pages
citing conflicting numbers for the same fact can be found by search.

Usage:
    # record a cited stat after a build (alongside ledger.py add for new sections)
    python optimizer/citations.py add blog/employee-training-best-practices \
        --stat "88% of organizations are worried about keeping people" \
        --source "LinkedIn 2025 Workplace Learning Report" --year 2025 \
        --url "https://learning.linkedin.com/resources/workplace-learning-report"

    # list everything, or one page's citations
    python optimizer/citations.py list
    python optimizer/citations.py list blog/employee-training-best-practices

    # stats at or past the freshness cutoff (proactive: "aging" == exactly at the
    # cutoff year, i.e. stale as soon as MIN_STAT_YEAR next increments)
    python optimizer/citations.py stale

    # pairs of citations that likely describe the same fact with different numbers
    python optimizer/citations.py conflicts

Stored at data/citations.json.
"""
import argparse
import json
import os
import re
import sys
from datetime import date

try:
    from constants import STOP_WORDS as STOP, MIN_STAT_YEAR
    from jsonstore import locked
except ImportError:
    from optimizer.constants import STOP_WORDS as STOP, MIN_STAT_YEAR
    from optimizer.jsonstore import locked

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(BASE, "data", "citations.json")


def _tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def _leading_number(s):
    """The first number (int/float, % or not) in a stat string, or None."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", s or "")
    return float(m.group(0).replace(",", "")) if m else None


def load():
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def save(data):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    tmp = f"{LEDGER}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LEDGER)


def add(slug, stat, source, year, url):
    entry = {
        "page_slug": slug,
        "stat": stat,
        "source": source or "",
        "year": int(year) if year else None,
        "url": url or "",
        "date_added": date.today().isoformat(),
    }
    with locked(LEDGER):
        data = load()
        data["entries"].append(entry)
        save(data)
    print(f"Citation recorded for {slug}: \"{stat}\" ({source}, {year})")
    return 0


def list_entries(slug=None):
    data = load()
    rows = [e for e in data["entries"] if not slug or slug.lower() in e["page_slug"].lower()]
    if not rows:
        print("Citation ledger is empty." if not slug else f"No citations for '{slug}'.")
        return 0
    for e in rows:
        print(f'  [{e["date_added"]}] {e["page_slug"]}: "{e["stat"]}" '
              f'({e.get("source","")}, {e.get("year","?")})')
    return 0


def stale_or_aging(entries, min_year=MIN_STAT_YEAR):
    """(stale, aging): entries whose year is already below min_year, and entries
    exactly at min_year - the latter are one MIN_STAT_YEAR bump away from
    becoming stale, so they're the ones to refresh proactively, before the
    reactive stale_stat_years() check in qa_check.py would even flag them."""
    stale, aging = [], []
    for e in entries:
        y = e.get("year")
        if y is None:
            continue
        if y < min_year:
            stale.append(e)
        elif y == min_year:
            aging.append(e)
    return stale, aging


def find_conflicts(entries):
    """Pairs of citations that likely describe the same fact with a different
    number: high token overlap in the stat text (or the same source) but a
    different leading number, from different pages. Returns [(entry_a, entry_b), ...].
    A heuristic, not proof - always spot-check before treating it as a real conflict.
    """
    conflicts = []
    for i, a in enumerate(entries):
        na = _leading_number(a["stat"])
        if na is None:
            continue
        ta = _tokens(a["stat"])
        for b in entries[i + 1:]:
            if a["page_slug"] == b["page_slug"]:
                continue
            nb = _leading_number(b["stat"])
            if nb is None or nb == na:
                continue
            same_source = a.get("source") and a["source"] == b.get("source")
            overlap = len(ta & _tokens(b["stat"]))
            if same_source or overlap >= 3:
                conflicts.append((a, b))
    return conflicts


def _cli_stale(min_year):
    stale, aging = stale_or_aging(load()["entries"], min_year)
    if not stale and not aging:
        print(f"No citations at or below the {min_year} freshness cutoff.")
        return 0
    if stale:
        print(f"STALE (year < {min_year}):")
        for e in stale:
            print(f'  [{e["year"]}] {e["page_slug"]}: "{e["stat"]}"')
    if aging:
        print(f"\nAGING (year == {min_year}, stale as soon as the cutoff moves):")
        for e in aging:
            print(f'  [{e["year"]}] {e["page_slug"]}: "{e["stat"]}"')
    return 1


def _cli_conflicts():
    conflicts = find_conflicts(load()["entries"])
    if not conflicts:
        print("No likely stat conflicts found.")
        return 0
    print(f"{len(conflicts)} likely conflict(s) - verify before treating as real:\n")
    for a, b in conflicts:
        print(f'  {a["page_slug"]}: "{a["stat"]}" ({a.get("source","")})')
        print(f'  {b["page_slug"]}: "{b["stat"]}" ({b.get("source","")})')
        print()
    return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("slug")
    a.add_argument("--stat", required=True)
    a.add_argument("--source", default="")
    a.add_argument("--year", type=int, default=None)
    a.add_argument("--url", default="")

    l = sub.add_parser("list")
    l.add_argument("slug", nargs="?", default=None)

    s = sub.add_parser("stale")
    s.add_argument("--min-year", type=int, default=MIN_STAT_YEAR)

    sub.add_parser("conflicts")

    args = ap.parse_args()
    if args.cmd == "add":
        sys.exit(add(args.slug, args.stat, args.source, args.year, args.url))
    if args.cmd == "list":
        sys.exit(list_entries(args.slug))
    if args.cmd == "stale":
        sys.exit(_cli_stale(args.min_year))
    if args.cmd == "conflicts":
        sys.exit(_cli_conflicts())
