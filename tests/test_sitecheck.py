"""Tests for the site-wide sitemap-coverage + crawl checks (optimizer/sitecheck.py).

Network is injected, so these never touch the wire. Runs under the default config
(base_url https://www.example.com/).
"""
import json

import sitecheck


AUDIT_DATA = {
    "money_pages": [{"name": "Course A", "url": "https://www.example.com/course-a"}],
    "blog_pages": [{"slug": "blog/post-1", "title": "Post 1"}, "blog/post-2"],
}


def _write_audit(tmp_path, monkeypatch, data):
    p = tmp_path / "audit.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(sitecheck, "AUDIT", str(p))


class TestInventoryUrls:
    def test_combines_money_and_blog_pages(self, tmp_path, monkeypatch):
        _write_audit(tmp_path, monkeypatch, AUDIT_DATA)
        urls = sitecheck.inventory_urls()
        assert "https://www.example.com/course-a" in urls
        assert "https://www.example.com/blog/post-1" in urls
        assert "https://www.example.com/blog/post-2" in urls

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sitecheck, "AUDIT", str(tmp_path / "nope.json"))
        assert sitecheck.inventory_urls() == []

    def test_dedupes(self, tmp_path, monkeypatch):
        data = {"money_pages": [], "blog_pages": ["blog/x", "blog/x/"]}
        _write_audit(tmp_path, monkeypatch, data)
        assert sitecheck.inventory_urls().count("https://www.example.com/blog/x") == 1


class TestSitemapParsing:
    def test_parses_urlset(self):
        xml = "<urlset><url><loc>https://x.com/a</loc></url><url><loc>https://x.com/b</loc></url></urlset>"
        locs, is_index = sitecheck.parse_sitemap(xml)
        assert locs == ["https://x.com/a", "https://x.com/b"]
        assert is_index is False

    def test_detects_sitemap_index(self):
        xml = '<sitemapindex><sitemap><loc>https://x.com/sitemap-1.xml</loc></sitemap></sitemapindex>'
        locs, is_index = sitecheck.parse_sitemap(xml)
        assert locs == ["https://x.com/sitemap-1.xml"]
        assert is_index is True

    def test_recurses_one_level_into_index(self):
        pages = {
            "https://x.com/sitemap.xml": '<sitemapindex><sitemap><loc>https://x.com/child.xml</loc></sitemap></sitemapindex>',
            "https://x.com/child.xml": "<urlset><url><loc>https://x.com/page-1</loc></url></urlset>",
        }
        urls = sitecheck.all_sitemap_urls("https://x.com/sitemap.xml", fetcher=lambda u: pages[u])
        assert urls == ["https://x.com/page-1"]


class TestSitemapCoverage:
    def test_finds_missing_and_orphaned(self):
        inv = ["https://x.com/a", "https://x.com/b"]
        sm = ["https://x.com/b", "https://x.com/c"]
        missing, orphaned = sitecheck.sitemap_coverage(inv, sm)
        assert missing == ["https://x.com/a"]
        assert orphaned == ["https://x.com/c"]

    def test_trailing_slash_insensitive(self):
        missing, orphaned = sitecheck.sitemap_coverage(["https://x.com/a/"], ["https://x.com/a"])
        assert missing == [] and orphaned == []

    def test_perfect_match_is_empty(self):
        urls = ["https://x.com/a", "https://x.com/b"]
        assert sitecheck.sitemap_coverage(urls, urls) == ([], [])


def _fake_status_fetcher(mapping):
    def fetch(url):
        status, final = mapping[url]
        return status, final, None
    return fetch


class TestCrawl:
    def test_classifies_each_url(self):
        mapping = {
            "https://x.com/a": (200, "https://x.com/a"),
            "https://x.com/b": (404, "https://x.com/b"),
        }
        results = sitecheck.crawl(list(mapping), fetcher=_fake_status_fetcher(mapping))
        verdicts = {url: v for url, v, _, _ in results}
        assert verdicts["https://x.com/a"] == "ok"
        assert verdicts["https://x.com/b"] == "broken"


class TestRunSitemap:
    def test_run_sitemap_reports_mismatch(self, tmp_path, monkeypatch, capsys):
        _write_audit(tmp_path, monkeypatch, AUDIT_DATA)
        sitemap_xml = "<urlset><url><loc>https://www.example.com/course-a</loc></url></urlset>"
        rc = sitecheck.run_sitemap("https://www.example.com/sitemap.xml", fetcher=lambda u: sitemap_xml)
        assert rc == 1
        out = capsys.readouterr().out
        assert "MISSING from sitemap" in out

    def test_run_sitemap_passes_on_full_match(self, tmp_path, monkeypatch):
        data = {"money_pages": [{"name": "A", "url": "https://www.example.com/a"}], "blog_pages": []}
        _write_audit(tmp_path, monkeypatch, data)
        sitemap_xml = "<urlset><url><loc>https://www.example.com/a</loc></url></urlset>"
        rc = sitecheck.run_sitemap("https://www.example.com/sitemap.xml", fetcher=lambda u: sitemap_xml)
        assert rc == 0

    def test_run_sitemap_reports_fetch_error(self, tmp_path, monkeypatch):
        _write_audit(tmp_path, monkeypatch, AUDIT_DATA)
        def boom(u):
            raise TimeoutError("timed out")
        assert sitecheck.run_sitemap("https://www.example.com/sitemap.xml", fetcher=boom) == 1


class TestRunCrawl:
    def test_run_crawl_flags_broken_page(self, tmp_path, monkeypatch):
        data = {"money_pages": [{"name": "A", "url": "https://www.example.com/a"}], "blog_pages": []}
        _write_audit(tmp_path, monkeypatch, data)
        mapping = {"https://www.example.com/a": (404, "https://www.example.com/a")}
        assert sitecheck.run_crawl(fetcher=_fake_status_fetcher(mapping)) == 1

    def test_run_crawl_passes_when_all_ok(self, tmp_path, monkeypatch):
        data = {"money_pages": [{"name": "A", "url": "https://www.example.com/a"}], "blog_pages": []}
        _write_audit(tmp_path, monkeypatch, data)
        mapping = {"https://www.example.com/a": (200, "https://www.example.com/a")}
        assert sitecheck.run_crawl(fetcher=_fake_status_fetcher(mapping)) == 0

    def test_run_crawl_no_pages(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sitecheck, "AUDIT", str(tmp_path / "nope.json"))
        assert sitecheck.run_crawl() == 0
        assert "No money/blog pages" in capsys.readouterr().out
