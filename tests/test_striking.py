"""Tests for the striking-distance report (optimizer/striking.py)."""
import striking


PAGES = [
    {"slug": "a", "position": 3.0, "impressions": 90000},    # top 3, not striking
    {"slug": "b", "position": 9.5, "impressions": 40000},    # striking, high imp
    {"slug": "c", "position": 15.0, "impressions": 5000},    # striking
    {"slug": "d", "position": 12.0, "impressions": 50},      # striking pos but too few imp
    {"slug": "e", "position": 45.0, "impressions": 8000},    # too deep
]


def test_selects_position_band_and_min_impressions():
    hits = striking.striking_pages(PAGES, lo=8, hi=20, min_impressions=100)
    slugs = [p["slug"] for p in hits]
    assert slugs == ["b", "c"]  # b before c (more impressions); d excluded (imp<100)


def test_custom_band():
    hits = striking.striking_pages(PAGES, lo=1, hi=20, min_impressions=100)
    assert "a" in [p["slug"] for p in hits]  # pos 3 now included


def test_empty_when_none_qualify():
    assert striking.striking_pages(PAGES, lo=21, hi=30, min_impressions=100) == []
