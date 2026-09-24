"""Tests for the citation-provenance ledger (optimizer/citations.py)."""
import citations


def _use_temp_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(citations, "LEDGER", str(tmp_path / "citations.json"))


def test_add_then_list(tmp_path, monkeypatch, capsys):
    _use_temp_ledger(tmp_path, monkeypatch)
    citations.add("blog/a", "88% of firms worry about retention", "LinkedIn 2025", 2025, "https://x.com")
    data = citations.load()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["year"] == 2025

    citations.list_entries()
    out = capsys.readouterr().out
    assert "blog/a" in out and "88%" in out


def test_list_filters_by_slug(tmp_path, monkeypatch, capsys):
    _use_temp_ledger(tmp_path, monkeypatch)
    citations.add("blog/a", "stat A", "Source A", 2025, "")
    citations.add("blog/b", "stat B", "Source B", 2025, "")
    capsys.readouterr()
    citations.list_entries("blog/a")
    out = capsys.readouterr().out
    assert "blog/a" in out and "blog/b" not in out


def test_list_empty(tmp_path, monkeypatch, capsys):
    _use_temp_ledger(tmp_path, monkeypatch)
    citations.list_entries()
    assert "empty" in capsys.readouterr().out.lower()


class TestLeadingNumber:
    def test_extracts_percent(self):
        assert citations._leading_number("88% of firms worry") == 88.0

    def test_extracts_decimal(self):
        assert citations._leading_number("a 3.5x increase") == 3.5

    def test_extracts_comma_thousands(self):
        assert citations._leading_number("cost $102,800 total") == 102800.0

    def test_no_number_returns_none(self):
        assert citations._leading_number("no numbers here") is None


class TestStaleOrAging:
    def test_below_cutoff_is_stale(self):
        entries = [{"year": 2022, "page_slug": "a", "stat": "x"}]
        stale, aging = citations.stale_or_aging(entries, min_year=2024)
        assert stale == entries and aging == []

    def test_at_cutoff_is_aging(self):
        entries = [{"year": 2024, "page_slug": "a", "stat": "x"}]
        stale, aging = citations.stale_or_aging(entries, min_year=2024)
        assert stale == [] and aging == entries

    def test_above_cutoff_is_neither(self):
        entries = [{"year": 2026, "page_slug": "a", "stat": "x"}]
        stale, aging = citations.stale_or_aging(entries, min_year=2024)
        assert stale == [] and aging == []

    def test_missing_year_ignored(self):
        entries = [{"year": None, "page_slug": "a", "stat": "x"}]
        assert citations.stale_or_aging(entries, min_year=2024) == ([], [])


class TestFindConflicts:
    def test_same_source_different_number_flagged(self):
        entries = [
            {"page_slug": "a", "stat": "40% of skills are obsolete in five years", "source": "Right Management"},
            {"page_slug": "b", "stat": "35% of skills are obsolete in five years", "source": "Right Management"},
        ]
        conflicts = citations.find_conflicts(entries)
        assert len(conflicts) == 1

    def test_high_overlap_different_source_flagged(self):
        entries = [
            {"page_slug": "a", "stat": "88 percent of firms worry about retention", "source": "LinkedIn"},
            {"page_slug": "b", "stat": "72 percent of firms worry about retention", "source": "Gallup"},
        ]
        conflicts = citations.find_conflicts(entries)
        assert len(conflicts) == 1

    def test_same_page_never_conflicts_with_itself(self):
        entries = [
            {"page_slug": "a", "stat": "40% obsolete", "source": "X"},
            {"page_slug": "a", "stat": "35% obsolete", "source": "X"},
        ]
        assert citations.find_conflicts(entries) == []

    def test_same_number_is_not_a_conflict(self):
        entries = [
            {"page_slug": "a", "stat": "40% of skills obsolete", "source": "X"},
            {"page_slug": "b", "stat": "40% of skills obsolete", "source": "X"},
        ]
        assert citations.find_conflicts(entries) == []

    def test_unrelated_stats_not_flagged(self):
        entries = [
            {"page_slug": "a", "stat": "40% of skills obsolete", "source": "X"},
            {"page_slug": "b", "stat": "12 practices for training success", "source": "Y"},
        ]
        assert citations.find_conflicts(entries) == []
