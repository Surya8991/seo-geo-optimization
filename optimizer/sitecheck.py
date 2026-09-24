#!/usr/bin/env python3
"""
Site-wide checks that need the full page inventory (data/audit.json), not just the
one page being optimized:

  * sitemap  - cross-reference audit.json's money/blog pages against the live
    sitemap.xml: pages missing from the sitemap (orphans) and sitemap entries
    missing from the inventory (stale/deleted pages still listed) are both bugs.
  * crawl    - fetch every money/blog page URL from the inventory and flag any
    404 or redirect, not just links inside the one page currently being
    optimized (that's linkcheck.py's job).

Network is injectable so the logic is testable.

Usage:
    python optimizer/sitecheck.py sitemap https://www.edstellar.com/sitemap.xml
    python optimizer/sitecheck.py crawl
"""
import json
import os
import re
import sys
import urllib.request

try:
    from config_loader import CONFIG
    from constants import small_inventory_warning
    from linkcheck import fetch_status, classify
except ImportError:
    from optimizer.config_loader import CONFIG
    from optimizer.constants import small_inventory_warning
    from optimizer.linkcheck import fetch_status, classify

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(BASE, "data", "audit.json")
BASE_URL = CONFIG["base_url"].rstrip("/") + "/"


def inventory_urls():
    """All money_page + blog_page URLs from data/audit.json, deduped, no trailing
    slash. Blog pages are stored as bare slugs and resolved against base_url;
    money pages already carry a full url."""
    if not os.path.exists(AUDIT):
        return []
    data = json.load(open(AUDIT, encoding="utf-8"))
    urls = []
    for mp in data.get("money_pages", []):
        u = (mp or {}).get("url", "").strip()
        if u:
            urls.append(u.rstrip("/"))
    for b in data.get("blog_pages", []):
        slug = (b.get("slug") if isinstance(b, dict) else b) or ""
        slug = str(slug).strip()
        if slug:
            urls.append((BASE_URL + slug.lstrip("/")).rstrip("/"))
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "seo-geo-sitecheck/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse_sitemap(xml_text):
    """(locs, is_index): <loc> URLs, and whether this is a <sitemapindex> (whose
    <loc>s are child sitemaps to fetch, not pages) rather than a <urlset>."""
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml_text, re.I)
    is_index = "<sitemapindex" in xml_text.lower()
    return locs, is_index


def all_sitemap_urls(root_sitemap_url, fetcher=fetch, max_children=50):
    """Fetch a sitemap (or sitemap index, recursing one level into its children)
    and return the flattened list of page URLs."""
    locs, is_index = parse_sitemap(fetcher(root_sitemap_url))
    if not is_index:
        return locs
    urls = []
    for child in locs[:max_children]:
        child_locs, _ = parse_sitemap(fetcher(child))
        urls.extend(child_locs)
    return urls


def sitemap_coverage(inv_urls, sitemap_urls):
    """(missing_from_sitemap, orphaned_in_sitemap): inventory pages absent from
    the sitemap, and sitemap pages absent from the inventory. Both directions are
    real bugs - trailing-slash insensitive."""
    inv = {u.rstrip("/") for u in inv_urls}
    sm = {u.rstrip("/") for u in sitemap_urls}
    return sorted(inv - sm), sorted(sm - inv)


def crawl(urls, fetcher=fetch_status):
    """Fetch every URL and classify it 'ok'/'redirect'/'broken' - the same rules
    linkcheck.py uses for links inside one page, applied across the whole site
    inventory instead. Returns [(url, verdict, final_url, error), ...]."""
    out = []
    for url in urls:
        status, final_url, error = fetcher(url)
        out.append((url, classify(url, status, final_url, error), final_url, error))
    return out


def run_sitemap(sitemap_url, fetcher=fetch):
    inv = inventory_urls()
    warning = small_inventory_warning(len(inv), "audit.json")
    if warning:
        print(warning)
    try:
        sm_urls = all_sitemap_urls(sitemap_url, fetcher=fetcher)
    except Exception as e:
        print(f"Could not fetch {sitemap_url} ({type(e).__name__}): {e}")
        return 1
    missing, orphaned = sitemap_coverage(inv, sm_urls)
    print(f"\nSitemap coverage: {len(inv)} inventory pages, {len(sm_urls)} sitemap pages\n")
    if missing:
        print(f"MISSING from sitemap ({len(missing)}) - not discoverable via sitemap:")
        for u in missing:
            print(f"  - {u}")
    if orphaned:
        print(f"\nIN sitemap but NOT in the inventory ({len(orphaned)}) - stale/deleted pages?")
        for u in orphaned[:20]:
            print(f"  - {u}")
    if not missing and not orphaned:
        print("Inventory and sitemap match.")
    return 1 if (missing or orphaned) else 0


def run_crawl(fetcher=fetch_status):
    urls = inventory_urls()
    warning = small_inventory_warning(len(urls), "audit.json")
    if warning:
        print(warning)
    if not urls:
        print("No money/blog pages in audit.json to crawl.")
        return 0
    print(f"\nCrawling {len(urls)} site page(s) from the inventory\n")
    problems = 0
    for url, verdict, final_url, error in crawl(urls, fetcher):
        if verdict == "ok":
            print(f"  [OK      ] {url}")
        elif verdict == "redirect":
            problems += 1
            print(f"  [REDIRECT] {url}\n             -> {final_url}")
        else:
            problems += 1
            print(f"  [BROKEN  ] {url}  ({error or 'HTTP error'})")
    print(f"\n{problems} page(s) need fixing." if problems else "\nAll inventory pages are live and canonical.")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("sitemap", "crawl"):
        print("Usage: python optimizer/sitecheck.py sitemap <sitemap-url>")
        print("       python optimizer/sitecheck.py crawl")
        sys.exit(2)
    if sys.argv[1] == "sitemap":
        if len(sys.argv) < 3:
            print("Usage: python optimizer/sitecheck.py sitemap <sitemap-url>")
            sys.exit(2)
        sys.exit(run_sitemap(sys.argv[2]))
    sys.exit(run_crawl())
