"""Tests for the llms.txt generator (optimizer/llms_txt.py)."""
import llms_txt


def test_builds_expected_sections():
    out = llms_txt.build_llms_txt(
        brand="Acme",
        base_url="https://acme.com/",
        content_rows=[{"title": "Agile Guide", "url": "https://acme.com/info/agile"}],
        money_pages=[{"name": "Scrum Course", "url": "https://acme.com/scrum/"}],
        tagline="Training that sticks.",
    )
    assert out.startswith("# Acme")
    assert "> Training that sticks." in out
    assert "## Key pages" in out
    assert "- [Scrum Course](https://acme.com/scrum/)" in out
    assert "## Content" in out
    assert "- [Agile Guide](https://acme.com/info/agile)" in out


def test_slug_falls_back_to_base_url():
    out = llms_txt.build_llms_txt("Acme", "https://acme.com/",
                                  [{"title": "X", "slug": "info/x"}], [])
    assert "https://acme.com/info/x" in out


def test_empty_inventory_still_has_title():
    out = llms_txt.build_llms_txt("Acme", "https://acme.com/", [], [])
    assert out.strip() == "# Acme"
