#!/usr/bin/env python3
"""
"What should I optimize next?" - rank the pages by priority score that have not
been built yet, so the manual one-page-at-a-time queue is driven by the data.

A page counts as DONE when a matching file exists in `final output/` (either
`<slug-tail>-green.html` or `<slug-tail>.html`) or its slug appears in the content
ledger. Everything else is pending, sorted by priority_score (highest first).

After the pending list it also prints the rest of the lifecycle, so nothing is left to
memory: pages built but with no publish date recorded, and published pages whose ~30-day
verification pass (WORKFLOW Step 9) is due or overdue.

Usage:
    python optimizer/next.py            # top 10 pending pages
    python optimizer/next.py 25         # top 25
"""
import json
import os
import re
import sys
from datetime import date

try:
    import verify
    from constants import small_inventory_warning
except ImportError:
    from optimizer import verify
    from optimizer.constants import small_inventory_warning

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORECARD = os.path.join(BASE, "data", "scorecard.json")
LEDGER = os.path.join(BASE, "data", "content_ledger.json")
FINAL_DIR = os.path.join(BASE, "final output")


def slug_tail(slug):
    """The last path segment of a slug/url, lowercased (info/foo -> foo)."""
    return re.sub(r"/+$", "", str(slug)).rsplit("/", 1)[-1].lower()


def done_slugs(final_files, ledger_entries):
    """Set of slug tails already built (from final-output filenames + ledger)."""
    done = set()
    for name in final_files:
        if not name.lower().endswith(".html"):
            continue
        base = re.sub(r"\.html$", "", name, flags=re.I)
        base = re.sub(r"-green$", "", base, flags=re.I)
        done.add(base.lower())
    for e in ledger_entries:
        done.add(slug_tail(e.get("page_slug", "")))
    done.discard("")
    return done


def pending_pages(pages, done):
    """Pages whose slug tail is not in `done`, sorted by priority_score desc."""
    out = [p for p in pages if slug_tail(p.get("slug") or p.get("url", "")) not in done]
    return sorted(out, key=lambda p: p.get("priority_score", 0), reverse=True)


def built_slugs(final_files):
    """Slug tails of pages with a file in `final output/` (ledger entries excluded)."""
    return {re.sub(r"(-green)?\.html$", "", n, flags=re.I).lower()
            for n in final_files if n.lower().endswith(".html")}


def unpublished(final_files, published):
    """Built pages with no recorded publish date, sorted."""
    pub = {verify._tail(p["page_slug"]) for p in published}
    return sorted(built_slugs(final_files) - pub)


def _load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def main(n):
    if not os.path.exists(SCORECARD):
        print(f"ERROR: {SCORECARD} not found. Run build_scorecard.py or copy scorecard.example.json.")
        return 1
    pages = _load_json(SCORECARD, {}).get("pages", [])
    ledger_entries = _load_json(LEDGER, {}).get("entries", [])
    final_files = os.listdir(FINAL_DIR) if os.path.isdir(FINAL_DIR) else []

    done = done_slugs(final_files, ledger_entries)
    pend = pending_pages(pages, done)

    print(f"\n{len(pend)} pending / {len(pages)} total pages ({len(done)} already built).")
    warning = small_inventory_warning(len(pages), "scorecard.json")
    if warning:
        print(warning)
    print(f"Top {min(n, len(pend))} to optimize next (by priority):\n")
    for p in pend[:n]:
        print(f"  [{p.get('priority_score', 0):>3}] {p.get('category', '?'):<22} "
              f"{p.get('action', ''):<9} {p.get('slug') or p.get('url')}")
        title = p.get("title", "")
        if title:
            print(f'        "{title}"  (clicks16m={p.get("clicks_16m","?")}, pos={p.get("position","?")})')
    print()

    log = verify.load()
    waiting = unpublished(final_files, log["published"])
    if waiting:
        print("Built, no publish date recorded (run `verify.py publish <slug>` once live):")
        for slug in waiting:
            print(f"  {slug}")
        print()
    queue = verify.due_items(log["published"], log["entries"], date.today())
    if queue:
        print("Post-publish verification (WORKFLOW Step 9):")
        verify.print_due(queue)
        print()
    return 0


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10
    sys.exit(main(n))
