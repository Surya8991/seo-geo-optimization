"""Regression tests for the public-repo review findings (dash counting, FAQ scope,
brand word boundaries, rolling stat year, meta unescape, sentence split, --json,
BOM handling)."""
import json
from datetime import date

import constants
import qa_check
from test_qa_run import _passing_optimize_html, _write


class TestDashCount:
    def test_literal_em_dash_counted_once(self):
        assert qa_check.count_dashes("<p>one — two</p>") == (1, 0)

    def test_entity_and_json_escape_each_counted_once(self):
        html = '<p>a &mdash; b &#8211; c</p><script>{"t":"x \\u2014 y"}</script>'
        assert qa_check.count_dashes(html) == (2, 1)

    def test_no_dashes(self):
        assert qa_check.count_dashes("<p>plain - hyphen</p>") == (0, 0)


FAQ_MICRODATA = """
<div itemscope itemtype="https://schema.org/Person"><span itemprop="name">Jane Doe</span></div>
<section class="faq" itemscope itemtype="https://schema.org/FAQPage">
  <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
    <p itemprop="name">Q1?</p>
    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer"><p itemprop="text">A1.</p></div>
  </div>
  <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
    <p itemprop="name">Q2?</p>
    <div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer"><p itemprop="text">A2.</p></div>
  </div>
</section>
<div itemscope itemtype="https://schema.org/Question"><p itemprop="name">Outside FAQ?</p></div>
"""


class TestFaqCount:
    def test_author_name_and_outside_question_not_counted(self):
        assert qa_check.faq_microdata_count(FAQ_MICRODATA) == (2, True)

    def test_no_faqpage_scope_counts_zero(self):
        html = '<span itemprop="name">Jane</span><div itemscope itemtype="https://schema.org/Question"></div>'
        assert qa_check.faq_microdata_count(html) == (0, False)

    def test_jsonld_counts_only_faqpage_main_entity(self):
        html = ('<script type="application/ld+json">{"@type":"FAQPage","mainEntity":['
                '{"@type":"Question","name":"a"},{"@type":"Question","name":"b"}]}</script>'
                '<script type="application/ld+json">{"@type":"QAPage","mainEntity":'
                '{"@type":"Question","name":"c"}}</script>')
        assert qa_check.faq_jsonld_count(html) == (2, True)

    def test_jsonld_graph_supported(self):
        html = ('<script type="application/ld+json">{"@graph":[{"@type":"Article"},'
                '{"@type":"FAQPage","mainEntity":{"@type":"Question","name":"a"}}]}</script>')
        assert qa_check.faq_jsonld_count(html) == (1, True)

    def test_author_itemprop_name_does_not_break_match(self, tmp_path):
        html = _passing_optimize_html().replace(
            "<h2>Conclusion</h2>",
            '<p itemscope itemtype="https://schema.org/Person">By <span itemprop="name">Jane Doe</span>.</p>\n'
            "<h2>Conclusion</h2>")
        path = _write(tmp_path, "page-green.html", html)
        report = qa_check.evaluate(path)
        faq = next(r for r in report["results"] if r["label"] == "FAQ HTML == JSON-LD count")
        assert faq["ok"], faq

    def test_faq_band_is_advisory_not_a_fail(self, tmp_path, monkeypatch):
        monkeypatch.setattr(qa_check, "FAQ_BAND", [(10 ** 9, 8, 10)])
        path = _write(tmp_path, "page-green.html", _passing_optimize_html())
        report = qa_check.evaluate(path)
        assert all(r["ok"] for r in report["results"])
        assert any("FAQ count outside" in w["label"] for w in report["warnings"])
        assert qa_check.run(path) == 0


class TestBrandMentions:
    def test_short_brand_needs_word_boundary(self):
        rx = qa_check.brand_pattern("Ace")
        assert qa_check.brand_mentions("Space to replace the race.", rx) == 0
        assert qa_check.brand_mentions("Ace helps. ACE again, ace's too.", rx) == 3

    def test_brand_with_punctuation(self):
        rx = qa_check.brand_pattern("Acme+")
        assert qa_check.brand_mentions("Try Acme+ today, not Acme+Pro.", rx) == 1

    def test_empty_brand(self):
        assert qa_check.brand_pattern("  ") is None


class TestMinStatYear:
    def test_rolling_default_tracks_today(self):
        assert constants.default_min_stat_year(date(2030, 6, 1)) == 2028
        assert constants.default_min_stat_year(date(2026, 1, 1)) == 2024

    def test_default_uses_current_year(self):
        assert constants.default_min_stat_year() == date.today().year - constants.STAT_YEAR_WINDOW

    def test_config_override_wins(self):
        assert constants.resolve_min_stat_year({"min_stat_year": 2020}) == 2020

    def test_null_override_falls_back(self):
        today = date(2031, 3, 3)
        assert constants.resolve_min_stat_year({"min_stat_year": None}, today) == 2029

    def test_freshness_relative_to_min_year(self):
        y = date.today().year
        assert qa_check.has_freshness_signal("", f"Last updated May {y}.", min_year=y - 2)
        assert not qa_check.has_freshness_signal("", f"Last updated May {y - 3}.", min_year=y - 2)


class TestMetaUnescape:
    def test_entities_measured_as_rendered(self, tmp_path):
        # Raw source is 62 chars; rendered (what the SERP shows) is 54.
        title = "Product &amp; Service Certification &amp; Training Guide 2026"
        assert len(title) > 60
        html = _passing_optimize_html().replace(
            "<strong>Meta title (32/60):</strong> Product Certification Guide 2026",
            f"<strong>Meta title (55/60):</strong> {title}")
        path = _write(tmp_path, "page-green.html", html)
        report = qa_check.evaluate(path)
        mt = next(r for r in report["results"] if r["label"].startswith("Meta title"))
        assert mt["ok"], mt


class TestSentenceSplit:
    def test_decimal_not_split(self):
        assert len(qa_check.split_sentences("Scores rose 4.5 points. Then fell.")) == 2

    def test_abbreviations_not_split(self):
        text = "Use tools, e.g. a matrix, i.e. a grid, vs. a list. Done."
        assert len(qa_check.split_sentences(text)) == 2

    def test_etc_mid_sentence_vs_end(self):
        assert len(qa_check.split_sentences("Pens, paper, etc. are fine. Ok.")) == 2
        assert len(qa_check.split_sentences("Pens, paper, etc. Next one.")) == 2


class TestJsonOutputAndBom:
    def test_json_output(self, tmp_path, capsys):
        path = _write(tmp_path, "page-green.html", _passing_optimize_html())
        assert qa_check.main([path, "--json"]) == 0
        data = json.loads(capsys.readouterr().out)
        assert data["passed"] is True
        assert data["mode"] == "optimize"
        assert {"results", "warnings", "info", "words", "link_band"} <= set(data)

    def test_bom_file_passes(self, tmp_path):
        p = tmp_path / "bom-green.html"
        p.write_text(_passing_optimize_html(), encoding="utf-8-sig")
        assert qa_check.run(str(p)) == 0


class TestBotLists:
    def test_current_retrieval_bots(self):
        import check_bots
        for bot in ("Claude-User", "Claude-SearchBot", "OAI-SearchBot", "ChatGPT-User",
                    "PerplexityBot", "Perplexity-User", "Bingbot"):
            assert bot in check_bots.RETRIEVAL_BOTS
        assert "Claude-Web" not in check_bots.RETRIEVAL_BOTS
        assert "Claude-Web" in check_bots.RETIRED_BOTS

    def test_training_bots(self):
        import check_bots
        for bot in ("GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot",
                    "meta-externalagent"):
            assert bot in check_bots.TRAINING_BOTS

    def test_retired_agent_named_in_robots_is_reported(self, capsys):
        import check_bots
        groups = check_bots.parse_robots("User-agent: Claude-Web\nDisallow: /\n")
        assert check_bots.report(groups) == 0
        assert "Retired user agents" in capsys.readouterr().out


class TestConfigExampleFallback:
    def test_missing_config_falls_back_to_example(self, tmp_path, monkeypatch, capsys):
        import config_loader
        (tmp_path / "config.example.json").write_text(
            '{"brand_name": "Acme", "domain": "example.com"}', encoding="utf-8")
        monkeypatch.delenv("SEO_GEO_CONFIG", raising=False)
        monkeypatch.setattr(config_loader, "project_root", lambda: str(tmp_path))
        cfg = config_loader.load_config()
        assert cfg["brand_name"] == "Acme"
        assert "config.example.json" in capsys.readouterr().err

    def test_committed_example_is_brand_neutral(self, monkeypatch):
        import config_loader
        monkeypatch.setenv("SEO_GEO_CONFIG", config_loader.example_config_path())
        cfg = config_loader.load_config()
        assert cfg["domain"] == "example.com"
        assert "{slug}" in cfg["money_page_pattern"]


class TestCli:
    def test_help_lists_commands(self, capsys):
        import cli
        assert cli.main(["--help"]) == 0
        out = capsys.readouterr().out
        assert "qa" in out and "build-scorecard" in out

    def test_unknown_command(self, capsys):
        import cli
        assert cli.main(["nope"]) == 2

    def test_alias_resolves_to_script(self):
        import cli
        assert cli.resolve("qa_check") == cli.resolve("qa")
        assert cli.resolve("qa").endswith("qa_check.py")

    def test_qa_dispatch_returns_exit_code(self, tmp_path, capsys):
        import cli
        path = _write(tmp_path, "page-green.html", _passing_optimize_html())
        assert cli.main(["qa", path, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["passed"] is True
        bad = _write(tmp_path, "bad-green.html", _passing_optimize_html().replace(
            "A direct answer opens the section.", "A direct answer — opens it."))
        assert cli.main(["qa", bad]) == 1
