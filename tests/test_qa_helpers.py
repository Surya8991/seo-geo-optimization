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
