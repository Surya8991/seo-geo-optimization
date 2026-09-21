#!/usr/bin/env python3
"""
Generate an /llms.txt from the site inventory (audit.json).

NOTE (2026): llms.txt is NOT a citation lever. Google ignores it and no major AI
vendor reads it in production; ML analysis found it adds noise to citation prediction.
It IS useful for IDE/MCP coding agents and some in-product assistants, and it is cheap
to ship, so this generator exists for that narrow purpose, not for AI-search ranking.

Usage:
    python optimizer/llms_txt.py                      # print to stdout
    python optimizer/llms_txt.py > llms.txt           # write the file
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


def build_llms_txt(brand, base_url, content_rows, money_pages, tagline=None):
    """Assemble llms.txt markdown: title, optional summary, money pages, key content."""
    lines = [f"# {brand}"]
    if tagline:
        lines.append(f"> {tagline}")
    lines.append("")
    if money_pages:
        lines.append("## Key pages")
        for mp in money_pages:
            name = mp.get("name") or mp.get("url", "")
            url = mp.get("url", "")
            lines.append(f"- [{name}]({url})")
        lines.append("")
    if content_rows:
        lines.append("## Content")
        for r in content_rows:
            title = r.get("title") or r.get("slug", "")
            url = r.get("url") or (base_url.rstrip("/") + "/" + r.get("slug", ""))
            lines.append(f"- [{title}]({url})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    if not os.path.exists(AUDIT):
        print(f"ERROR: {AUDIT} not found. Run build_scorecard.py or copy audit.example.json.",
              file=sys.stderr)
        return 1
    data = json.load(open(AUDIT, encoding="utf-8"))
    rows = data.get("audit_rows", [])
    money = data.get("money_pages", [])
    out = build_llms_txt(CONFIG.get("brand_name", ""), CONFIG.get("base_url", ""), rows, money)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
