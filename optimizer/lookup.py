#!/usr/bin/env python3
"""
Step 1 helper: pull everything the pipeline knows about one page into a single brief.

Usage:
    python optimizer/lookup.py <slug-or-url-fragment>
    python optimizer/lookup.py product-certification
    python optimizer/lookup.py "agile scrum"

Merges the scorecard row (performance + category + trend) with the audit row
(primary keyword, search intent, money page) and prints a plain-text brief, plus
the lever the numbers point to (high impressions + low CTR = title/meta;
low position = depth).
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORECARD = os.path.join(BASE, "data", "scorecard.json")
AUDIT = os.path.join(BASE, "data", "audit.json")


def find(rows, frag, keys):
    frag = frag.lower().strip().rstrip("/")
    hits = []
    for r in rows:
        hay = " ".join(str(r.get(k, "")) for k in keys).lower()
        if frag in hay:
            hits.append(r)
    return hits


def interpret(sc):
    """Turn the numbers into the lever to pull."""
    notes = []
    ctr = sc.get("ctr")
    pos = sc.get("position")
    cat = sc.get("category", "")
    trend = sc.get("trend_label", "")
    imp = sc.get("impressions", 0)
    if imp and ctr is not None and ctr < 1 and imp > 100000:
        notes.append(f"HIGH impressions ({imp:,}) + LOW CTR ({ctr}%) -> title/meta/snippet is the lever, not more content.")
    if pos is not None and pos > 10:
        notes.append(f"Avg position {pos} (page 2+) -> needs depth, authority, internal links to climb.")
    elif pos is not None and 4 <= pos <= 10:
        notes.append(f"Avg position {pos} (page 1, below fold) -> freshness + snippet targeting to move up.")
    if isinstance(trend, str) and trend.lower() == "declining":
        notes.append("Declining trend -> content decay; refresh stats and re-match intent.")
    lever = {
        "Dead Since Birth": "Near-complete rewrite: new angle, structure, fresh content.",
        "Quick Win": "Targeted fixes: add missing sections, fix keywords, add FAQ.",
        "Lost Momentum": "Content refresh: update stats, add sections, improve depth.",
        "Top Performers Falling": "Careful updates: do not break what works, add freshness.",
        "Performing Well": "Light touch: update date, refresh stats, add FAQ if missing.",
    }.get(cat)
    if lever:
        notes.append(f"Category '{cat}' -> {lever}")
    return notes


def show(title, val):
    print(f"  {title:<22}: {val}")


def main(frag):
    if not os.path.exists(SCORECARD):
        print(f"ERROR: scorecard file not found: {SCORECARD}")
        print("Run 'python build_scorecard.py' first, or add data/scorecard.json.")
        return 1
    if not os.path.exists(AUDIT):
        print(f"ERROR: audit file not found: {AUDIT}")
        return 1

    sc_data = json.load(open(SCORECARD, encoding="utf-8")).get("pages", [])
    au_data = json.load(open(AUDIT, encoding="utf-8")).get("audit_rows", [])

    sc_hits = find(sc_data, frag, ["url", "slug", "title"])
    au_hits = find(au_data, frag, ["url", "slug", "title", "primary_keyword"])

    if not sc_hits and not au_hits:
        print(f"No match for '{frag}'.")
        return 1
    if len(sc_hits) > 1 or len(au_hits) > 1:
        print(f"'{frag}' is ambiguous. Matches:")
        for r in (sc_hits or au_hits):
            print("   -", r.get("url") or r.get("slug"))
        print("Narrow the fragment.")
        return 1

    sc = sc_hits[0] if sc_hits else {}
    au = au_hits[0] if au_hits else {}

    print("\n" + "=" * 70)
    print("PAGE BRIEF:", (au.get("title") or au.get("name") or sc.get("title") or frag))
    print("=" * 70)

    print("\n-- SCORECARD (performance) --")
    if sc:
        show("URL", sc.get("url"))
        show("Slug", sc.get("slug"))
        show("Category", sc.get("category"))
        show("Priority score", sc.get("priority_score"))
        show("Action", sc.get("action"))
        show("Clicks (16m)", sc.get("clicks_16m"))
        show("Impressions", f"{sc.get('impressions'):,}" if sc.get("impressions") else "-")
        show("CTR %", sc.get("ctr"))
        pos = sc.get("position")
        pos_band = sc.get("pos_band", "")
        show("Avg position", f"{pos} ({pos_band})" if pos else "-")
        trend_label = sc.get("trend_label", "")
        trend_pct = sc.get("trend_pct", "")
        show("Trend", f"{trend_label} ({trend_pct}%)" if trend_label else "-")
        show("Monthly clicks", sc.get("monthly"))
    else:
        print("  (no scorecard row)")

    print("\n-- AUDIT (strategy) --")
    if au:
        show("Primary keyword", au.get("primary_keyword"))
        show("Meta title", au.get("meta_title"))
        show("Meta description", au.get("meta_description"))
        show("H1 tag", au.get("h1_tag"))
        show("Search intent", au.get("search_intent"))
        show("Money page", au.get("money_page"))
        show("Money page name", au.get("money_page_name"))
    else:
        print("  (no audit row)")

    print("\n-- WHAT THE DATA SAYS (lever) --")
    for n in interpret(sc):
        print("  *", n)
    print()
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
