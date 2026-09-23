#!/usr/bin/env python3
"""
Internal-link resolver for a built page: extract every internal link from the
reader body (review/publishing/changes notes excluded) and confirm each one
resolves to a live, canonical URL. Catches two problems the other gates miss:

  * BROKEN  - the target 404s or errors (a dead internal link).
  * REDIRECT - the target 301/302s to a different URL (a stale slug). Linking to a
    redirect wastes link equity and points readers at a non-canonical URL; link to
    the final URL instead.

Domain/base_url come from config.json. Network is injectable so the logic is testable.

Usage:
    python optimizer/linkcheck.py "final output/<slug>-green.html"
"""
import re
import sys
import urllib.request
import urllib.error
from urllib.parse import urljoin

from config_loader import CONFIG
from qa_check import strip_note_blocks

DOMAIN = re.sub(r"^www\.", "", CONFIG["domain"].lower())
BASE_URL = CONFIG["base_url"].rstrip("/") + "/"


def extract_internal_links(html):
    """Unique internal link hrefs from the reader body, in document order.

    Internal = same domain or a root-relative path. Skips #anchors, mailto:, tel:,
    and Cloudflare email-protection links.
    """
    body = strip_note_blocks(html)
    hrefs = re.findall(r'<a\s[^>]*href="([^"]+)"[^>]*>', body, re.I)
    seen, out = set(), []
    for h in hrefs:
        hl = h.strip()
        if not hl or hl.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if "/cdn-cgi/l/email-protection" in hl:
            continue
        is_internal = hl.startswith("/") or DOMAIN in hl.lower()
        if not is_internal:
            continue
        absolute = urljoin(BASE_URL, hl)
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def classify(url, status, final_url, error=None):
    """Pure verdict for one link: 'ok' | 'redirect' | 'broken'."""
    if error is not None or status is None:
        return "broken"
    if status >= 400:
        return "broken"
    # 3xx, or a 200 whose final URL differs from the requested one, is a redirect.
    if 300 <= status < 400:
        return "redirect"
    if final_url and final_url.rstrip("/") != url.rstrip("/"):
        return "redirect"
    return "ok"


def fetch_status(url, timeout=15):
    """Return (status, final_url, error). Follows redirects; final_url reveals them."""
    req = urllib.request.Request(url, headers={"User-Agent": "seo-geo-linkcheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return getattr(r, "status", r.getcode()), r.geturl(), None
    except urllib.error.HTTPError as e:
        return e.code, getattr(e, "url", url), None
    except Exception as e:  # noqa: BLE001 - any network failure means we cannot confirm
        return None, url, str(e)


def run(path, fetcher=fetch_status):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    links = extract_internal_links(html)
    if not links:
        print("No internal links found in the reader body.")
        return 0

    print(f"Checking {len(links)} internal link(s) in {path}\n")
    problems = 0
    for url in links:
        status, final_url, error = fetcher(url)
        verdict = classify(url, status, final_url, error)
        if verdict == "ok":
            print(f"  [OK      ] {url}")
        elif verdict == "redirect":
            problems += 1
            print(f"  [REDIRECT] {url}\n             -> {final_url}  (link to the final URL)")
        else:
            detail = error or f"HTTP {status}"
            problems += 1
            print(f"  [BROKEN  ] {url}  ({detail})")

    if problems:
        print(f"\n{problems} internal link(s) need fixing (broken or redirecting). "
              "Point each at its live, canonical URL.")
        return 1
    print("\nAll internal links resolve to a live, canonical URL.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python optimizer/linkcheck.py \"final output/<slug>-green.html\"")
        sys.exit(2)
    sys.exit(run(sys.argv[1]))
