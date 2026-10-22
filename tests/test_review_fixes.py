"""Regression tests for the second deep-review round (qa_check, technical_seo,
linkcheck, check_bots, jsonstore, sitecheck, lookup)."""
import gzip
import json
import os
import time

import check_bots
import jsonstore
import linkcheck
import lookup
import qa_check
import sitecheck
import technical_seo


class TestQaDashes:
    def _dashes(self, body):
        h = f"<p>{body}</p>"
        import html as hl, re
        return len(re.findall(r"(?<!-)--(?!-)", qa_check.visible_dash_text(h)))

    def test_spaced_double_hyphen_caught(self):
        assert self._dashes("this -- that") == 1

    def test_unspaced_double_hyphen_caught(self):
        assert self._dashes("this--that") == 1

    def test_comment_and_css_vars_ignored(self):
        h = "<!-- note --><style>a{color:var(--x)}</style><p>fine</p>"
        assert "--" not in qa_check.visible_dash_text(h)

    def test_entity_dash_is_decoded(self):
        assert "—" in qa_check.visible_dash_text("<p>a &mdash; b</p>")


class TestQaReaderText:
    def test_remove_block_is_not_reader_text(self):
        h = '<p>keep</p><div class="remove-block"><span class="remove-tag">REMOVE</span><p>A 2019 study found 45%</p></div>'
        assert "2019" not in qa_check.reader_text(h)
        assert "keep" in qa_check.reader_text(h)

    def test_note_with_extra_classes_and_single_quotes(self):
        for tag in ('<div class="note publishing">', "<div class='note'>"):
            assert "secret" not in qa_check.strip_note_blocks(f"{tag}secret</div><p>x</p>")

    def test_new_tag_span_removed(self):
        assert "label" not in qa_check.strip_note_blocks('<span class="new-tag">label</span><p>x</p>')

    def test_footnote_class_not_treated_as_note(self):
        assert "kept" in qa_check.strip_note_blocks('<div class="footnote">kept</div>')


class TestQaLinks:
    def test_substring_domain_is_not_internal(self):
        assert not qa_check.is_internal_href("https://google.com/search?q=example.com")
        assert qa_check.is_external_href("https://google.com/search?q=example.com")

    def test_site_hosts_are_internal(self):
        assert qa_check.is_internal_href("https://www.example.com/x")
        assert qa_check.is_internal_href("https://blog.example.com/x")
        assert qa_check.is_internal_href("/relative")
        assert not qa_check.is_internal_href("https://notexample.com/x")

    def test_country_slug_detection(self, monkeypatch):
        monkeypatch.setattr(qa_check, "COUNTRY_SLUGS", {"australia"})
        assert qa_check.country_slug_in_href("/australia/") == "australia"
        assert qa_check.country_slug_in_href("https://www.example.com/australia?x=1") == "australia"
        assert qa_check.country_slug_in_href("https://other.com/australia/") is None
        assert qa_check.country_slug_in_href("/info/australia-guide") is None

    def test_conclusion_stops_at_next_h2(self):
        html = "<h2>Conclusion</h2><p>wrap up</p><h2>FAQ</h2><p>widget</p>"
        kp = qa_check.keyword_placement(html, "x", "", "", "widget")
        assert kp["in_conclusion"] is False


class TestTechnicalSeoParsing:
    def test_noindex_with_content_before_name(self):
        assert technical_seo.is_noindexed('<meta content="noindex" name="robots">')

    def test_noindex_single_quotes(self):
        assert technical_seo.is_noindexed("<meta name='robots' content='noindex,follow'>")

    def test_googlebot_meta(self):
        assert technical_seo.is_noindexed('<meta name="googlebot" content="noindex">')

    def test_lowercase_header(self):
        assert technical_seo.is_noindexed("<html></html>", {"x-robots-tag": "noindex"})

    def test_canonical_href_before_rel(self):
        html = '<link href="https://a.com/x" rel="canonical">'
        assert technical_seo.canonical_issues(html, "https://a.com/x") == []

    def test_hreflang_any_order(self):
        html = '<link href="https://a.com/fr" hreflang="fr" rel="alternate">'
        assert technical_seo.extract_hreflang_links(html) == {"fr": "https://a.com/fr"}


class TestBreadcrumbShapes:
    def _html(self, payload):
        return f'<script type="application/ld+json">{json.dumps(payload)}</script>'

    def test_array_payload(self):
        crumbs = {"@type": "BreadcrumbList", "itemListElement": [{"item": "/info/a"}]}
        assert linkcheck.extract_breadcrumb_links(self._html([crumbs]))

    def test_item_as_object_and_graph(self):
        crumbs = {"@type": ["BreadcrumbList"], "itemListElement": [{"item": {"@id": "/info/b"}}]}
        urls = linkcheck.extract_breadcrumb_links(self._html({"@graph": [crumbs]}))
        assert urls and urls[0].endswith("/info/b")


class TestRobotsMatching:
    def test_wildcard_disallow_blocks(self):
        g = check_bots.parse_robots("User-agent: *\nDisallow: /*")
        assert check_bots.agent_can_fetch(g, "PerplexityBot", "/") is False

    def test_dollar_anchor(self):
        g = check_bots.parse_robots("User-agent: *\nDisallow: /*.pdf$")
        assert check_bots.agent_can_fetch(g, "x", "/a.pdf") is False
        assert check_bots.agent_can_fetch(g, "x", "/a.pdf.html") is True

    def test_tie_prefers_allow(self):
        g = check_bots.parse_robots("User-agent: *\nDisallow: /a\nAllow: /a")
        assert check_bots.agent_can_fetch(g, "x", "/a") is True

    def test_googlebot_block_is_reported(self):
        g = check_bots.parse_robots("User-agent: Googlebot\nDisallow: /")
        assert check_bots.agent_can_fetch(g, "Googlebot", "/") is False
        assert "Googlebot" in check_bots.RETRIEVAL_BOTS


class TestJsonstoreLock:
    def test_creates_missing_directory(self, tmp_path):
        target = str(tmp_path / "newdir" / "x.json")
        with jsonstore.locked(target):
            assert os.path.isdir(tmp_path / "newdir")

    def test_stale_lock_is_broken(self, tmp_path):
        target = str(tmp_path / "x.json")
        lock = target + ".lock"
        open(lock, "w").close()
        old = time.time() - jsonstore.STALE_LOCK_SECONDS - 5
        os.utime(lock, (old, old))
        with jsonstore.locked(target, timeout=2):
            pass

    def test_fresh_lock_times_out(self, tmp_path):
        target = str(tmp_path / "x.json")
        open(target + ".lock", "w").close()
        try:
            with jsonstore.locked(target, timeout=0.2):
                raise AssertionError("should not acquire")
        except jsonstore.LockTimeout:
            pass


class TestSitecheck:
    def test_gzip_sitemap_decoded(self, monkeypatch):
        payload = gzip.compress(b"<urlset><url><loc>https://x.com/a</loc></url></urlset>")

        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return payload
        monkeypatch.setattr(sitecheck.urllib.request, "urlopen", lambda *a, **k: R())
        assert "https://x.com/a" in sitecheck.fetch("https://x.com/sitemap.xml.gz")

    def test_crawl_keeps_order(self):
        urls = [f"https://x.com/{i}" for i in range(20)]
        out = sitecheck.crawl(urls, fetcher=lambda u: (200, u, None))
        assert [o[0] for o in out] == urls


class TestLookupExactSlug:
    ROWS = [{"slug": "info/agile", "title": "Agile"},
            {"slug": "info/agile-scrum", "title": "Agile Scrum"}]

    def test_exact_slug_beats_substring(self):
        hits = lookup.find(self.ROWS, "info/agile", ["slug", "title"])
        assert [h["slug"] for h in hits] == ["info/agile"]

    def test_still_ambiguous_without_exact(self):
        assert len(lookup.find(self.ROWS, "agil", ["slug", "title"])) == 2
