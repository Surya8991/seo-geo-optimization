"""Tests for the content ledger (optimizer/ledger.py)."""
import ledger


def _use_temp_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER", str(tmp_path / "content_ledger.json"))


def test_add_then_list_and_search(tmp_path, monkeypatch, capsys):
    _use_temp_ledger(tmp_path, monkeypatch)

    ledger.add("info/training-roi", "How to measure training ROI",
               "formula + worked example", "ROI calculator table")
    data = ledger.load()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["page_slug"] == "info/training-roi"

    hits = ledger.search("training roi")
    assert hits, "expected the freshly added section to be found"
    assert hits[0][1]["section"] == "How to measure training ROI"

    ledger.list_entries()
    out = capsys.readouterr().out
    assert "training-roi" in out


def test_search_scores_exact_phrase_highest(tmp_path, monkeypatch):
    _use_temp_ledger(tmp_path, monkeypatch)
    ledger.add("p1", "Leadership styles compared", "", "")
    ledger.add("p2", "Training budgets and roi", "", "")

    hits = ledger.search("leadership styles")
    assert hits[0][1]["page_slug"] == "p1"
    assert hits[0][0] >= 100  # exact phrase present -> score bonus


def test_search_empty_ledger(tmp_path, monkeypatch):
    _use_temp_ledger(tmp_path, monkeypatch)
    assert ledger.search("anything") == []
