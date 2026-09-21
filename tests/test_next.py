"""Tests for the 'what to optimize next' ranking (optimizer/next.py)."""
import next as next_mod


PAGES = [
    {"slug": "info/alpha", "title": "Alpha", "priority_score": 90, "category": "Quick Win"},
    {"slug": "info/beta", "title": "Beta", "priority_score": 70, "category": "Lost Momentum"},
    {"slug": "info/gamma", "title": "Gamma", "priority_score": 50, "category": "Performing Well"},
]


def test_slug_tail():
    assert next_mod.slug_tail("info/product-certification") == "product-certification"
    assert next_mod.slug_tail("info/foo/") == "foo"
    assert next_mod.slug_tail("BAR") == "bar"


def test_done_slugs_from_files_and_ledger():
    done = next_mod.done_slugs(
        final_files=["alpha-green.html", "delta.html", "notes.txt"],
        ledger_entries=[{"page_slug": "info/beta"}],
    )
    assert "alpha" in done      # -green stripped
    assert "delta" in done      # plain .html
    assert "beta" in done       # from ledger
    assert "notes.txt" not in done  # .html not stripped -> stays, but harmless


def test_pending_excludes_done_and_sorts_by_priority():
    done = {"alpha"}  # alpha already built
    pend = next_mod.pending_pages(PAGES, done)
    assert [p["slug"] for p in pend] == ["info/beta", "info/gamma"]  # beta(70) before gamma(50)


def test_pending_empty_when_all_done():
    done = {"alpha", "beta", "gamma"}
    assert next_mod.pending_pages(PAGES, done) == []
