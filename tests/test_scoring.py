"""Tests for the pure scoring/parsing helpers in optimizer/scoring.py."""
import scoring


class TestCtrParsing:
    def test_percent_string_is_explicit(self):
        assert scoring.ctr_to_number("3.45%") == (3.45, True)

    def test_bare_number_not_explicit(self):
        assert scoring.ctr_to_number(0.0345) == (0.0345, False)

    def test_none_and_garbage(self):
        assert scoring.ctr_to_number(None) == (0.0, False)
        assert scoring.ctr_to_number("n/a") == (0.0, False)

    def test_fraction_column_detected(self):
        # GSC export: all values are 0-1 fractions -> should be scaled x100
        assert scoring.ctr_column_is_fraction([0.0345, 0.008, 0.12, 0.5]) is True
        assert scoring.normalise_ctr([0.0345, 0.008, 0.12, 0.5]) == 100

    def test_percent_column_detected(self):
        # Some value > 1.5 means the column is already in percent units -> no scaling
        assert scoring.ctr_column_is_fraction([3.45, 0.8, 12.0]) is False
        assert scoring.normalise_ctr([3.45, 0.8, 12.0]) == 1

    def test_ambiguous_sub_one_percent_column_stays_fraction(self):
        # This is the case the old per-value <1 heuristic got wrong. We now decide
        # per-column: an all-<=1 column is treated as fractions (GSC's real format).
        assert scoring.ctr_column_is_fraction([0.008, 0.004]) is True

    def test_empty_column_defaults_to_fraction(self):
        assert scoring.ctr_column_is_fraction([]) is True


class TestBands:
    def test_position_band(self):
        assert scoring.position_band(0) == "No Data"
        assert scoring.position_band(2) == "Top 3"
        assert scoring.position_band(7) == "Page 1 (4-10)"
        assert scoring.position_band(15) == "Page 2"
        assert scoring.position_band(40) == "Page 3+"
        assert scoring.position_band(80) == "Deep"

    def test_impression_band(self):
        assert scoring.impression_band(500000) == "Very High"
        assert scoring.impression_band(20000) == "High"
        assert scoring.impression_band(2000) == "Medium"
        assert scoring.impression_band(300) == "Low"
        assert scoring.impression_band(10) == "Very Low"

    def test_expected_ctr_monotonic(self):
        assert scoring.expected_ctr(1) > scoring.expected_ctr(3)
        assert scoring.expected_ctr(3) > scoring.expected_ctr(8)


class TestTrend:
    def test_needs_four_points(self):
        assert scoring.compute_trend({"a": 1, "b": 2}, ["a", "b"]) == 0.0

    def test_declining(self):
        labels = ["m1", "m2", "m3", "m4"]
        pct = scoring.compute_trend({"m1": 100, "m2": 100, "m3": 50, "m4": 50}, labels)
        assert pct == -50.0
        assert scoring.trend_label(pct) == "Declining"

    def test_rising(self):
        labels = ["m1", "m2", "m3", "m4"]
        pct = scoring.compute_trend({"m1": 50, "m2": 50, "m3": 100, "m4": 100}, labels)
        assert pct == 100.0
        assert scoring.trend_label(pct) == "Rising"

    def test_stable_label(self):
        assert scoring.trend_label(0.0) == "Stable"
        assert scoring.trend_label(10) == "Stable"


class TestIntent:
    def test_commercial(self):
        assert scoring.classify_intent("best-scrum-tools", "Best Scrum Tools") == "commercial"

    def test_navigational(self):
        assert scoring.classify_intent("portal-login", "Login Portal") == "navigational"

    def test_informational_default(self):
        assert scoring.classify_intent("what-is-agile", "What is Agile") == "informational"


class TestMoneyPagePattern:
    def test_matches_valid_slug(self):
        rx = scoring.money_page_pattern_regex("https://www.example.com/course/{course-slug}")
        assert rx.match("https://www.example.com/course/agile-scrum")
        assert rx.match("https://www.example.com/course/agile-scrum-101")

    def test_rejects_mismatched_url(self):
        rx = scoring.money_page_pattern_regex("https://www.example.com/course/{course-slug}")
        assert not rx.match("https://www.example.com/blog/agile-scrum")
        assert not rx.match("https://www.example.com/course/agile-scrum/extra")

    def test_no_placeholder_returns_none(self):
        assert scoring.money_page_pattern_regex("https://www.example.com/courses") is None

    def test_trailing_slash_is_optional_either_side(self):
        # Pattern has no trailing slash but a real export URL does (and vice versa) ->
        # neither should be treated as a mismatch.
        rx = scoring.money_page_pattern_regex("https://www.example.com/course/{course-slug}")
        assert rx.match("https://www.example.com/course/agile-scrum/")

        rx2 = scoring.money_page_pattern_regex("https://www.example.com/course/{course-slug}/")
        assert rx2.match("https://www.example.com/course/agile-scrum")


class TestHeaderIndex:
    def test_finds_by_exact_alias(self):
        idx, warning = scoring.header_index(["slug", "meta_title", "meta_description"],
                                             ["meta_title", "title"], 1)
        assert idx == 1 and warning is None

    def test_finds_by_second_alias(self):
        idx, warning = scoring.header_index(["slug", "title"], ["meta_title", "title"], 1)
        assert idx == 1 and warning is None

    def test_case_insensitive(self):
        idx, warning = scoring.header_index(["Slug", "Meta_Title"], ["meta_title"], 1)
        assert idx == 1 and warning is None

    def test_missing_header_falls_back_with_warning(self):
        idx, warning = scoring.header_index(["slug", "something_else"], ["meta_title", "title"], 1)
        assert idx == 1
        assert warning is not None and "not found" in warning

    def test_empty_header_row_falls_back_with_warning(self):
        idx, warning = scoring.header_index([], ["h1_tag", "h1"], 16)
        assert idx == 16
        assert warning is not None

    def test_none_cells_in_header_row_are_tolerated(self):
        idx, warning = scoring.header_index([None, "meta_title", None], ["meta_title"], 1)
        assert idx == 1 and warning is None


class TestSafeParsers:
    def test_safe_int(self):
        assert scoring.safe_int("42") == 42
        assert scoring.safe_int(None) == 0
        assert scoring.safe_int("x", default=-1) == -1

    def test_safe_float(self):
        assert scoring.safe_float("3.5") == 3.5
        assert scoring.safe_float(None) == 0.0
