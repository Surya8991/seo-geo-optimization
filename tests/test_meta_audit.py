"""Tests for the meta uniqueness audit (optimizer/meta_audit.py)."""
import meta_audit


ROWS = [
    {"slug": "info/a", "meta_title": "Guide to Scrum", "meta_description": "Learn scrum."},
    {"slug": "info/b", "meta_title": "guide to scrum", "meta_description": "Different desc."},
    {"slug": "info/c", "meta_title": "Product Certification", "meta_description": "Learn scrum."},
    {"slug": "info/d", "meta_title": "", "meta_description": ""},
]


def test_duplicate_titles_case_and_space_insensitive():
    dupes = meta_audit.find_duplicates(ROWS, "meta_title")
    assert "guide to scrum" in dupes
    assert set(dupes["guide to scrum"]) == {"info/a", "info/b"}
    assert "product certification" not in dupes  # unique


def test_duplicate_descriptions():
    dupes = meta_audit.find_duplicates(ROWS, "meta_description")
    assert set(dupes["learn scrum."]) == {"info/a", "info/c"}


def test_empty_values_ignored():
    dupes = meta_audit.find_duplicates(ROWS, "meta_title")
    assert "" not in dupes


def test_no_duplicates_returns_empty():
    rows = [{"slug": "x", "meta_title": "One"}, {"slug": "y", "meta_title": "Two"}]
    assert meta_audit.find_duplicates(rows, "meta_title") == {}
