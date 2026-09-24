#!/usr/bin/env python3
"""
Generate a /pricing.md skeleton from the site's money pages (data/audit.json).

Why: an AI agent evaluating a product or service on a buyer's behalf skips
vendors whose pricing is locked behind a JS-rendered page or a "contact sales"
wall it can't parse. A plain markdown file at the site root is trivially
parseable by any LLM - no rendering, no login wall (same principle as
robots.txt for crawlers or llms.txt for AI context).

This generates only the SKELETON - name + URL per money page, from the existing
inventory. It deliberately does NOT invent prices, limits, or features: fill
those in by hand with real, current figures before publishing, and keep it
updated - stale pricing is worse than no file. Link the finished file from the
sitemap and the main pricing page.

Usage:
    python optimizer/pricing.py                      # print to stdout
    python optimizer/pricing.py > pricing.md          # write the skeleton
"""
import json
import os
import sys

try:
    from config_loader import CONFIG
except ImportError:
    from optimizer.config_loader import CONFIG

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(BASE, "data", "audit.json")


def build_pricing_skeleton(brand, money_pages):
    """Markdown skeleton: one section per money page with {{fill in}} placeholders
    for price/limits/features - never invented figures."""
    lines = [f"# Pricing - {brand}", ""]
    if not money_pages:
        lines.append("<!-- No money_pages in data/audit.json yet - add them, then rerun. -->")
        return "\n".join(lines).rstrip() + "\n"
    for mp in money_pages:
        name = mp.get("name") or mp.get("url", "")
        url = mp.get("url", "")
        lines += [
            f"## {name}",
            "- Price: {{fill in - a real published rate, or a clear quote-based note}}",
            "- Limits: {{fill in - e.g. minimum group size, session length, seat count}}",
            "- Features: {{fill in - what's included at this tier}}",
            f"- URL: {url}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def main():
    if not os.path.exists(AUDIT):
        print(f"ERROR: {AUDIT} not found. Run build_scorecard.py or copy audit.example.json.",
              file=sys.stderr)
        return 1
    data = json.load(open(AUDIT, encoding="utf-8"))
    money = data.get("money_pages", [])
    out = build_pricing_skeleton(CONFIG.get("brand_name", ""), money)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
