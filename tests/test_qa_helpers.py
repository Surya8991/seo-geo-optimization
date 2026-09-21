"""Tests for the pure helpers in optimizer/qa_check.py (config-independent bits)."""
import re

import qa_check


class TestDomainPrefix:
    def test_www_prefix_stripped(self):
        assert re.sub(r"^www\.", "", "www.example.com") == "example.com"

    def test_w_leading_domain_not_mangled(self):
        # The old lstrip("www.") turned these into 'ine.com' / 'ashingtonpost.com'.
        assert re.sub(r"^www\.", "", "wine.com") == "wine.com"
        assert re.sub(r"^www\.", "", "washingtonpost.com") == "washingtonpost.com"
        assert re.sub(r"^www\.", "", "weforum.org") == "weforum.org"


class TestBritishSpellings:
    def test_flags_genuine_british(self):
        found = qa_check.find_british_spellings(
            "The colour and behaviour of the organisation under analysis."
        )
        assert "colour" in found
        assert "behaviour" in found
        assert any(w.startswith("organis") for w in found)

    def test_allows_american_ise_words(self):
        # These are correct American English and must NOT be flagged.
        text = ("We advertise and improvise; managers supervise, comprise the board, "
                "exercise judgment, and otherwise revise the enterprise franchise.")
        assert qa_check.find_british_spellings(text) == []

    def test_allows_ise_inflections(self):
        text = "They advertised, supervised, and improvised while advertising the course."
        assert qa_check.find_british_spellings(text) == []

    def test_flags_customise_but_not_customize(self):
        assert "customise" in qa_check.find_british_spellings("You can customise the plan.")
        assert qa_check.find_british_spellings("You can customize the plan.") == []


class TestLinkBand:
    def test_bands(self):
        assert qa_check.link_band(1500) == (4, 3)
        assert qa_check.link_band(3000) == (7, 4)
        assert qa_check.link_band(5000) == (9, 5)
        assert qa_check.link_band(9000) == (10, 6)


class TestFlesch:
    def test_simple_text_scores_higher_than_complex(self):
        simple = "The cat sat on the mat. The dog ran. We went home."
        complex_ = ("Notwithstanding the aforementioned considerations, the "
                    "multidimensional ramifications necessitate comprehensive evaluation.")
        assert qa_check.flesch_reading_ease(simple) > qa_check.flesch_reading_ease(complex_)

    def test_empty_returns_none(self):
        assert qa_check.flesch_reading_ease("") is None


class TestStripTags:
    def test_removes_scripts_styles_tags(self):
        html = "<style>x{}</style><p>Hello <b>world</b></p><script>var a=1;</script>"
        out = qa_check.strip_tags(html)
        assert "Hello" in out and "world" in out
        assert "var a" not in out and "x{}" not in out


class TestJsonLd:
    VALID = ('<script type="application/ld+json">'
             '{"@context":"https://schema.org","@type":"FAQPage"}</script>')
    BROKEN = ('<script type="application/ld+json">'
              '{"@type":"FAQPage",}</script>')  # trailing comma -> invalid JSON

    def test_extract_counts_blocks(self):
        assert len(qa_check.extract_jsonld_blocks(self.VALID + self.BROKEN)) == 2

    def test_valid_block_has_no_errors(self):
        assert qa_check.invalid_jsonld_blocks(self.VALID) == []

    def test_broken_block_is_reported(self):
        bad = qa_check.invalid_jsonld_blocks(self.VALID + self.BROKEN)
        assert len(bad) == 1
        assert bad[0][0] == 2  # the second block is the broken one


class TestHeadingHierarchy:
    def test_levels_extracted_in_order(self):
        html = "<h1>a</h1><h2>b</h2><h3>c</h3><h2>d</h2>"
        assert qa_check.heading_levels(html) == [1, 2, 3, 2]

    def test_valid_hierarchy_has_no_errors(self):
        assert qa_check.heading_hierarchy_errors([1, 2, 3, 2, 2]) == []

    def test_missing_h1_flagged(self):
        errs = qa_check.heading_hierarchy_errors([2, 3])
        assert any("H1" in e for e in errs)

    def test_two_h1_flagged(self):
        errs = qa_check.heading_hierarchy_errors([1, 2, 1])
        assert any("found 2" in e for e in errs)

    def test_skipped_level_flagged(self):
        errs = qa_check.heading_hierarchy_errors([1, 2, 4])
        assert any("skipped" in e for e in errs)

    def test_comments_ignored(self):
        html = "<!-- <h3>x</h3> --><h1>a</h1><h2>b</h2>"
        assert qa_check.heading_levels(html) == [1, 2]


class TestImageIssues:
    def test_missing_alt_flagged(self):
        assert qa_check.image_issues('<img src="/a/good-name.jpg">')  # no alt
        assert qa_check.image_issues('<img src="/a/x.jpg" alt="">')   # empty alt

    def test_good_image_passes(self):
        assert qa_check.image_issues('<img src="/img/scrum-board-example.jpg" alt="A scrum board">') == []

    def test_generic_filename_flagged(self):
        issues = qa_check.image_issues('<img src="/up/IMG_1234.jpg" alt="A chart">')
        assert any("generic" in i for i in issues)


class TestKeywordPlacement:
    HTML = ("<h1>Product Certification Guide</h1>"
            "<p>Product certification is a formal process.</p>"
            "<h2>Conclusion</h2><p>Choose product certification wisely.</p>")
    TEXT = ("Product certification is a formal process. Choose product certification wisely.")

    def test_reports_placement(self):
        kp = qa_check.keyword_placement(self.HTML, self.TEXT, "Product Certification Guide",
                                        "Product Certification Guide 2026", "product certification")
        assert kp["in_h1"] is True
        assert kp["in_title"] is True
        assert kp["in_first_100"] is True
        assert kp["in_conclusion"] is True
        assert kp["count"] == 2  # counted in reader text (H1 is separate)

    def test_conclusion_none_when_absent(self):
        kp = qa_check.keyword_placement("<h1>X</h1><p>x product certification</p>",
                                        "x product certification", "X", "X", "product certification")
        assert kp["in_conclusion"] is None
