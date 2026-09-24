"""Tests for the live noindex/canonical check (optimizer/technical_seo.py).

Network is injected, so these never touch the wire. Runs under the default config
(base_url https://www.example.com/).
"""
import technical_seo


class TestResolveUrl:
    def test_bare_slug_resolves_against_base_url(self):
        assert technical_seo.resolve_url("blog/post") == "https://www.example.com/blog/post"

    def test_absolute_url_used_as_is(self):
        assert technical_seo.resolve_url("https://other.com/x") == "https://other.com/x"


class TestNoindex:
    def test_meta_noindex_detected(self):
        html = '<meta name="robots" content="noindex, follow">'
        assert technical_seo.is_noindexed(html) is True

    def test_meta_index_follow_is_fine(self):
        html = '<meta name="robots" content="index, follow">'
        assert technical_seo.is_noindexed(html) is False

    def test_no_meta_tag_is_fine(self):
        assert technical_seo.is_noindexed("<html></html>") is False

    def test_x_robots_tag_header_detected(self):
        assert technical_seo.is_noindexed("<html></html>", {"X-Robots-Tag": "noindex"}) is True

    def test_other_headers_ignored(self):
        assert technical_seo.is_noindexed("<html></html>", {"Content-Type": "text/html"}) is False


class TestCanonical:
    def test_missing_canonical_flagged(self):
        assert technical_seo.canonical_issues("<html></html>", "https://x.com/a") == [
            'no <link rel="canonical"> tag found'
        ]

    def test_matching_canonical_passes(self):
        html = '<link rel="canonical" href="https://x.com/a">'
        assert technical_seo.canonical_issues(html, "https://x.com/a") == []

    def test_trailing_slash_insensitive(self):
        html = '<link rel="canonical" href="https://x.com/a/">'
        assert technical_seo.canonical_issues(html, "https://x.com/a") == []

    def test_mismatched_canonical_flagged(self):
        html = '<link rel="canonical" href="https://x.com/wrong-page">'
        issues = technical_seo.canonical_issues(html, "https://x.com/a")
        assert len(issues) == 1 and "wrong-page" in issues[0]

    def test_multiple_canonical_tags_flagged(self):
        html = ('<link rel="canonical" href="https://x.com/a">'
                '<link rel="canonical" href="https://x.com/b">')
        issues = technical_seo.canonical_issues(html, "https://x.com/a")
        assert any("2 canonical tags" in i for i in issues)


class TestHreflang:
    def test_extracts_hreflang_href_first_order(self):
        html = '<link rel="alternate" hreflang="en-us" href="https://x.com/us">'
        assert technical_seo.extract_hreflang_links(html) == {"en-us": "https://x.com/us"}

    def test_extracts_href_hreflang_reversed_order(self):
        html = '<link rel="alternate" href="https://x.com/us" hreflang="en-us">'
        assert technical_seo.extract_hreflang_links(html) == {"en-us": "https://x.com/us"}

    def test_no_hreflang_tags_returns_empty(self):
        assert technical_seo.extract_hreflang_links("<html></html>") == {}

    def test_issues_empty_when_no_hreflang_at_all(self):
        assert technical_seo.hreflang_issues("<html></html>", "https://x.com/a") == []

    def test_missing_self_reference_flagged(self):
        html = '<link rel="alternate" hreflang="en-us" href="https://x.com/us">'
        issues = technical_seo.hreflang_issues(html, "https://x.com/a")
        assert any("self-referencing" in i for i in issues)

    def test_missing_x_default_flagged(self):
        html = '<link rel="alternate" hreflang="en-us" href="https://x.com/a">'
        issues = technical_seo.hreflang_issues(html, "https://x.com/a")
        assert any("x-default" in i for i in issues)

    def test_complete_hreflang_set_has_no_issues(self):
        html = ('<link rel="alternate" hreflang="en-us" href="https://x.com/a">'
                '<link rel="alternate" hreflang="x-default" href="https://x.com/a">')
        assert technical_seo.hreflang_issues(html, "https://x.com/a") == []


def test_main_passes_when_clean():
    def fake_fetch(url):
        return '<link rel="canonical" href="https://www.example.com/blog/post">', {}
    assert technical_seo.main("blog/post", fetcher=fake_fetch) == 0


def test_main_fails_on_noindex_and_bad_canonical():
    def fake_fetch(url):
        html = ('<meta name="robots" content="noindex">'
                '<link rel="canonical" href="https://www.example.com/other">')
        return html, {}
    assert technical_seo.main("blog/post", fetcher=fake_fetch) == 1


def test_main_reports_fetch_failure():
    def fake_fetch(url):
        raise TimeoutError("timed out")
    assert technical_seo.main("blog/post", fetcher=fake_fetch) == 1
