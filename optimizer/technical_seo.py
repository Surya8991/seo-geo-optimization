#!/usr/bin/env python3
"""
Live technical-SEO check: fetch a page's actually-served HTML/headers and confirm
it is not accidentally deindexed and carries a correct, singular canonical tag.

qa_check.py works on the pre-publish review-copy draft, which never carries these
site-template-level tags (they're injected by the CMS at publish time) - so those
two common, easy-to-miss bugs need a live check instead. Network is injectable so
the logic is testable.

Usage:
    python optimizer/technical_seo.py https://www.edstellar.com/blog/some-post
    python optimizer/technical_seo.py blog/some-post   # resolved against base_url
"""
import re
import sys
import urllib.request

from config_loader import CONFIG

BASE_URL = CONFIG["base_url"].rstrip("/") + "/"

_ROBOTS_META_RE = re.compile(r'<meta\s+name="robots"[^>]*content="([^"]*)"', re.I)
_CANONICAL_RE = re.compile(r'<link\s+rel="canonical"[^>]*href="([^"]*)"', re.I)
_HREFLANG_RE_A = re.compile(r'<link\s+rel="alternate"[^>]*hreflang="([^"]+)"[^>]*href="([^"]*)"', re.I)
_HREFLANG_RE_B = re.compile(r'<link\s+rel="alternate"[^>]*href="([^"]*)"[^>]*hreflang="([^"]+)"', re.I)


def resolve_url(target):
    """A bare slug resolves against base_url; anything with a scheme is used as-is."""
    return target if "://" in target else BASE_URL + target.lstrip("/")


def is_noindexed(html, headers=None):
    """True if a meta robots tag or an X-Robots-Tag response header contains
    'noindex' - a page silently dropped from the index is worse than a bad rank."""
    for m in _ROBOTS_META_RE.finditer(html):
        if "noindex" in m.group(1).lower():
            return True
    if headers and "noindex" in (headers.get("X-Robots-Tag") or "").lower():
        return True
    return False


def canonical_issues(html, expected_url):
    """Problems with the page's canonical tag(s): missing, more than one, or
    pointing somewhere other than the page's own URL (trailing-slash insensitive)."""
    hrefs = _CANONICAL_RE.findall(html)
    issues = []
    if not hrefs:
        issues.append('no <link rel="canonical"> tag found')
        return issues
    if len(hrefs) > 1:
        issues.append(f"{len(hrefs)} canonical tags found, expected exactly 1: {hrefs}")
    norm_expected = expected_url.rstrip("/")
    for href in hrefs:
        if href.rstrip("/") != norm_expected:
            issues.append(f"canonical points to {href!r}, expected {expected_url!r}")
    return issues


def extract_hreflang_links(html):
    """{lang_code: href} from <link rel="alternate" hreflang="..." href="...">
    tags, tolerant of attribute order. lang codes are lowercased ('x-default'
    included as-is)."""
    out = {}
    for lang, href in _HREFLANG_RE_A.findall(html):
        out[lang.lower()] = href
    for href, lang in _HREFLANG_RE_B.findall(html):
        out.setdefault(lang.lower(), href)
    return out


def hreflang_issues(html, expected_url):
    """Problems with this page's hreflang set, for a page that HAS hreflang tags
    at all (a page with none simply isn't part of an hreflang set - not itself a
    bug to report here). Checks: a self-referencing entry exists, and an
    'x-default' fallback exists - both are common, easy-to-miss requirements for
    a correct multi-region/language hreflang implementation."""
    links = extract_hreflang_links(html)
    if not links:
        return []
    issues = []
    if not any(href.rstrip("/") == expected_url.rstrip("/") for href in links.values()):
        issues.append("no self-referencing hreflang entry (a page must list itself)")
    if "x-default" not in links:
        issues.append("no x-default hreflang entry")
    return issues


def fetch(url, timeout=15):
    """Return (html, headers). headers is a case-insensitive-ish plain dict."""
    req = urllib.request.Request(url, headers={"User-Agent": "seo-geo-technical-check/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace"), dict(r.headers)


def main(target, fetcher=fetch):
    url = resolve_url(target)
    print(f"Fetching {url} ...")
    try:
        html, headers = fetcher(url)
    except Exception as e:
        print(f"Could not fetch {url} ({type(e).__name__}): {e}")
        return 1

    ok = True
    if is_noindexed(html, headers):
        ok = False
        print("  [FAIL] Page is noindexed (meta robots or X-Robots-Tag) - it will not be indexed at all.")
    else:
        print("  [OK  ] Not noindexed")

    issues = canonical_issues(html, url)
    if issues:
        ok = False
        print("  [FAIL] Canonical tag issue(s):")
        for i in issues:
            print(f"           - {i}")
    else:
        print("  [OK  ] Canonical tag present, singular, and self-referencing")

    hreflang = extract_hreflang_links(html)
    if hreflang:
        hl_issues = hreflang_issues(html, url)
        if hl_issues:
            ok = False
            print(f"  [FAIL] hreflang issue(s) ({len(hreflang)} entries found):")
            for i in hl_issues:
                print(f"           - {i}")
        else:
            print(f"  [OK  ] hreflang set present and self-referencing ({len(hreflang)} entries)")
    else:
        print("  [--  ] No hreflang tags (fine for a page with no region/language variants)")

    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python optimizer/technical_seo.py <url-or-slug>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
