"""Tests for the internal-link resolver (optimizer/linkcheck.py).

Network is injected, so these never touch the wire. Runs under the default config
(domain example.com, base_url https://www.example.com/).
"""
import linkcheck


HTML = """<!DOCTYPE html><html><body><div class="wrap">
<div class="note">Review note with a <a href="https://www.example.com/should-be-ignored">note link</a>.</div>
<p>A <a href="/blog/live-page">live internal</a> link and an
<a href="https://www.example.com/blog/redirects">redirecting</a> one.</p>
<p>A <a href="https://www.example.com/blog/dead">dead</a> link, plus an
<a href="https://external.com/x" rel="nofollow" target="_blank">external</a> one and a
<a href="#faq">jump</a>.</p>
<div class="note" style="background:#eef7f0"><table><tr><td>
<a href="https://www.example.com/summary-only">summary note link</a></td></tr></table></div>
</div></body></html>"""


def test_extract_skips_notes_externals_and_anchors():
    links = linkcheck.extract_internal_links(HTML)
    assert links == [
        "https://www.example.com/blog/live-page",
        "https://www.example.com/blog/redirects",
        "https://www.example.com/blog/dead",
    ]
    # note links (both boxes), the external link, and the #anchor are all excluded
    assert all("should-be-ignored" not in u and "summary-only" not in u for u in links)
    assert all("external.com" not in u for u in links)


def test_classify_verdicts():
    ok = "https://www.example.com/a"
    assert linkcheck.classify(ok, 200, ok) == "ok"
    assert linkcheck.classify(ok, 200, ok + "/") == "ok"          # trailing slash is fine
    assert linkcheck.classify(ok, 301, "https://www.example.com/b") == "redirect"
    assert linkcheck.classify(ok, 200, "https://www.example.com/b") == "redirect"  # silent 301
    assert linkcheck.classify(ok, 404, ok) == "broken"
    assert linkcheck.classify(ok, None, ok, error="timeout") == "broken"


def _fake_fetcher(mapping):
    def fetch(url):
        status, final = mapping[url]
        return status, final, None
    return fetch


def test_run_fails_on_redirect_or_broken(tmp_path):
    p = tmp_path / "page-green.html"
    p.write_text(HTML, encoding="utf-8")
    mapping = {
        "https://www.example.com/blog/live-page": (200, "https://www.example.com/blog/live-page"),
        "https://www.example.com/blog/redirects": (200, "https://www.example.com/blog/canonical"),
        "https://www.example.com/blog/dead": (404, "https://www.example.com/blog/dead"),
    }
    assert linkcheck.run(str(p), fetcher=_fake_fetcher(mapping)) == 1


def test_run_passes_when_all_canonical(tmp_path):
    p = tmp_path / "page-green.html"
    p.write_text(HTML, encoding="utf-8")
    mapping = {
        "https://www.example.com/blog/live-page": (200, "https://www.example.com/blog/live-page"),
        "https://www.example.com/blog/redirects": (200, "https://www.example.com/blog/redirects"),
        "https://www.example.com/blog/dead": (200, "https://www.example.com/blog/dead"),
    }
    assert linkcheck.run(str(p), fetcher=_fake_fetcher(mapping)) == 0


BREADCRUMB_HTML = """<!DOCTYPE html><html><body><div class="wrap">
<p>No body links here at all, just text.</p>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Blog","item":"https://www.example.com/blog"},
  {"@type":"ListItem","position":2,"name":"Page","item":"https://www.example.com/blog/rotted"}
]}
</script>
</div></body></html>"""


class TestBreadcrumbLinks:
    def test_extracts_internal_breadcrumb_urls(self):
        links = linkcheck.extract_breadcrumb_links(BREADCRUMB_HTML)
        assert links == ["https://www.example.com/blog", "https://www.example.com/blog/rotted"]

    def test_non_breadcrumb_jsonld_is_ignored(self):
        html = '<script type="application/ld+json">{"@type":"Article","headline":"x"}</script>'
        assert linkcheck.extract_breadcrumb_links(html) == []

    def test_run_flags_a_broken_breadcrumb_link(self, tmp_path):
        p = tmp_path / "page.html"
        p.write_text(BREADCRUMB_HTML, encoding="utf-8")
        mapping = {
            "https://www.example.com/blog": (200, "https://www.example.com/blog"),
            "https://www.example.com/blog/rotted": (404, "https://www.example.com/blog/rotted"),
        }
        assert linkcheck.run(str(p), fetcher=_fake_fetcher(mapping)) == 1

    def test_run_passes_when_breadcrumb_links_are_canonical(self, tmp_path):
        p = tmp_path / "page.html"
        p.write_text(BREADCRUMB_HTML, encoding="utf-8")
        mapping = {
            "https://www.example.com/blog": (200, "https://www.example.com/blog"),
            "https://www.example.com/blog/rotted": (200, "https://www.example.com/blog/rotted"),
        }
        assert linkcheck.run(str(p), fetcher=_fake_fetcher(mapping)) == 0
