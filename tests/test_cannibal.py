"""Tests for cannibalization detection (optimizer/cannibal.py) against sample data."""
import os

import cannibal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE_SCORECARD = os.path.join(ROOT, "data", "scorecard.example.json")
EXAMPLE_AUDIT = os.path.join(ROOT, "data", "audit.example.json")


def _point_at_examples(monkeypatch):
    monkeypatch.setattr(cannibal, "SCORECARD", EXAMPLE_SCORECARD)
    monkeypatch.setattr(cannibal, "AUDIT", EXAMPLE_AUDIT)
    # Isolate the ledger so a developer's real ledger doesn't affect the result.
    if cannibal.ledger_search is not None:
        monkeypatch.setattr(cannibal, "ledger_search", lambda phrase: [])


def test_tokens_drops_stopwords():
    toks = cannibal.tokens("How to measure the best training ROI")
    assert "training" in toks
    assert "roi" in toks
    assert "the" not in toks and "best" not in toks and "how" not in toks


def test_finds_overlapping_existing_page(monkeypatch, capsys):
    _point_at_examples(monkeypatch)
    rc = cannibal.main("product certification", exclude=None)
    out = capsys.readouterr().out
    assert rc == 0
    assert "product-certification" in out
    assert "STRONG OVERLAP" in out  # exact phrase present in an existing page title


def test_no_match_is_safe_to_write(monkeypatch, capsys):
    _point_at_examples(monkeypatch)
    rc = cannibal.main("underwater basket weaving", exclude=None)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Safe to write a new section" in out


def test_exclude_filters_the_page_being_optimized(monkeypatch, capsys):
    _point_at_examples(monkeypatch)
    cannibal.main("product certification", exclude="product-certification")
    out = capsys.readouterr().out
    # The page under optimization is excluded, so its own row should not appear.
    assert "info/product-certification" not in out
