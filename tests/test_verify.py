"""Tests for the post-publish verification log (optimizer/verify.py)."""
import verify


def _use_temp_log(tmp_path, monkeypatch):
    monkeypatch.setattr(verify, "LOG", str(tmp_path / "verification_log.json"))


def test_build_cited_maps_engines():
    cited = verify.build_cited("chatgpt, perplexity", "gemini,claude")
    assert cited == {"chatgpt": True, "perplexity": True, "gemini": False, "claude": False}


def test_build_cited_handles_empty():
    assert verify.build_cited("", "") == {}


def test_add_then_list(tmp_path, monkeypatch, capsys):
    _use_temp_log(tmp_path, monkeypatch)
    verify.add("info/product-certification", "product certification",
               {"chatgpt": True, "gemini": False}, "+0.4", "-3", "yes", "cited in AIO")
    data = verify.load()
    assert len(data["entries"]) == 1
    e = data["entries"][0]
    assert e["page_slug"] == "info/product-certification"
    assert e["cited"] == {"chatgpt": True, "gemini": False}
    assert e["ai_overview"] == "yes"

    verify.list_entries("product-certification")
    out = capsys.readouterr().out
    assert "product-certification" in out
    assert "chatgpt=y" in out and "gemini=n" in out


def test_list_empty(tmp_path, monkeypatch, capsys):
    _use_temp_log(tmp_path, monkeypatch)
    verify.list_entries()
    assert "empty" in capsys.readouterr().out.lower()


def test_summarize_aggregates_engine_rates_and_deltas():
    entries = [
        {"page_slug": "a", "cited": {"chatgpt": True, "gemini": False},
         "ai_overview": "yes", "ctr_delta": "+0.4", "pos_delta": "-3"},
        {"page_slug": "b", "cited": {"chatgpt": True, "gemini": True},
         "ai_overview": "no", "ctr_delta": "-0.2", "pos_delta": "-1"},
    ]
    s = verify.summarize(entries)
    assert s["pages"] == 2 and s["entries"] == 2
    assert s["engine_rates"]["chatgpt"] == (2, 2)   # cited in both
    assert s["engine_rates"]["gemini"] == (1, 2)    # cited in one
    assert s["ai_overview"] == (1, 2)
    assert s["avg_ctr_delta"] == 0.1                # (0.4 + -0.2) / 2
    assert s["avg_pos_delta"] == -2.0               # (-3 + -1) / 2


def test_summarize_empty():
    s = verify.summarize([])
    assert s["entries"] == 0 and s["engine_rates"] == {}
