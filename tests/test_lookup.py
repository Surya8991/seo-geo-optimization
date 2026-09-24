"""Tests for the Step 1 page-brief helper (optimizer/lookup.py)."""
import lookup


ROWS = [
    {"url": "https://example.com/info/agile-scrum", "slug": "info/agile-scrum", "title": "Agile Scrum Guide"},
    {"url": "https://example.com/info/agile-coaching", "slug": "info/agile-coaching", "title": "Agile Coaching"},
    {"url": "https://example.com/info/six-sigma", "slug": "info/six-sigma", "title": "Six Sigma Basics"},
]


class TestFind:
    def test_single_match_by_slug_fragment(self):
        hits = lookup.find(ROWS, "six-sigma", ["url", "slug", "title"])
        assert [r["slug"] for r in hits] == ["info/six-sigma"]

    def test_ambiguous_fragment_returns_multiple(self):
        hits = lookup.find(ROWS, "agile", ["url", "slug", "title"])
        assert len(hits) == 2

    def test_no_match_returns_empty(self):
        assert lookup.find(ROWS, "nonexistent-topic", ["url", "slug", "title"]) == []

    def test_fragment_is_case_and_slash_insensitive(self):
        hits = lookup.find(ROWS, "SIX-SIGMA/", ["url", "slug", "title"])
        assert len(hits) == 1

    def test_matches_on_title_not_just_slug(self):
        hits = lookup.find(ROWS, "coaching", ["url", "slug", "title"])
        assert [r["slug"] for r in hits] == ["info/agile-coaching"]


class TestInterpret:
    def test_high_impressions_low_ctr_flags_title_meta_lever(self):
        notes = lookup.interpret({"impressions": 200000, "ctr": 0.5, "position": 3})
        assert any("title/meta" in n for n in notes)

    def test_page_two_plus_flags_depth_lever(self):
        notes = lookup.interpret({"position": 15})
        assert any("depth" in n for n in notes)

    def test_page_one_below_fold_flags_freshness_lever(self):
        notes = lookup.interpret({"position": 7})
        assert any("freshness" in n for n in notes)

    def test_top_three_position_triggers_neither_band(self):
        notes = lookup.interpret({"position": 2})
        assert not any("depth" in n or "freshness" in n for n in notes)

    def test_declining_trend_flags_decay(self):
        notes = lookup.interpret({"trend_label": "Declining"})
        assert any("decay" in n for n in notes)

    def test_category_maps_to_lever_text(self):
        notes = lookup.interpret({"category": "Quick Win"})
        assert any("Targeted fixes" in n for n in notes)

    def test_unknown_category_adds_no_lever_note(self):
        notes = lookup.interpret({"category": "Not A Real Category"})
        assert not any("->" in n and "Category" in n for n in notes)

    def test_empty_scorecard_row_returns_no_notes(self):
        assert lookup.interpret({}) == []
