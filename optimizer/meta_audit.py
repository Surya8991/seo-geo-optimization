#!/usr/bin/env python3
"""
Meta uniqueness audit: find duplicate meta titles and meta descriptions across the
site. Duplicate metas split relevance signals and get rewritten by Google, so each
page should have its own. Reads data/audit.json (built by build_scorecard.py).

Usage:
    python optimizer/meta_audit.py
"""
import json
import os
import sys

try:
    from constants import small_inventory_warning
except ImportError:
    from optimizer.constants import small_inventory_warning

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(BASE, "data", "audit.json")


def _norm(s):
    return " ".join(str(s or "").split()).strip().lower()


def find_duplicates(rows, field):
    """Map normalized value -> [slugs] for values shared by more than one page."""
    by_value = {}
    for r in rows:
        val = _norm(r.get(field, ""))
        if not val:
            continue
        by_value.setdefault(val, []).append(r.get("slug") or r.get("url", "?"))
    return {v: slugs for v, slugs in by_value.items() if len(slugs) > 1}


def _report(rows, field, label):
    dupes = find_duplicates(rows, field)
    if not dupes:
        print(f"  No duplicate {label}.")
        return 0
    print(f"  {len(dupes)} duplicated {label}:")
    for val, slugs in sorted(dupes.items(), key=lambda x: -len(x[1])):
        preview = (val[:70] + "...") if len(val) > 70 else val
        print(f'    "{preview}"')
        for s in slugs:
            print(f"        - {s}")
    return 1


def main():
    if not os.path.exists(AUDIT):
        print(f"ERROR: {AUDIT} not found. Run build_scorecard.py or copy audit.example.json.")
        return 1
    rows = json.load(open(AUDIT, encoding="utf-8")).get("audit_rows", [])
    print(f"\nMeta uniqueness audit across {len(rows)} pages\n")
    warning = small_inventory_warning(len(rows), "audit.json")
    if warning:
        print(warning + "\n")
    print("Meta titles:")
    rc_t = _report(rows, "meta_title", "meta titles")
    print("\nMeta descriptions:")
    rc_d = _report(rows, "meta_description", "meta descriptions")
    print()
    return 1 if (rc_t or rc_d) else 0


if __name__ == "__main__":
    sys.exit(main())
