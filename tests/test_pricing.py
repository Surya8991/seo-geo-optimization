"""Tests for the pricing.md skeleton generator (optimizer/pricing.py)."""
import pricing


def test_builds_one_section_per_money_page():
    out = pricing.build_pricing_skeleton("Acme", [
        {"name": "Scrum Course", "url": "https://acme.com/scrum/"},
        {"name": "Kanban Course", "url": "https://acme.com/kanban/"},
    ])
    assert out.startswith("# Pricing - Acme")
    assert "## Scrum Course" in out
    assert "## Kanban Course" in out
    assert "https://acme.com/scrum/" in out
    assert "https://acme.com/kanban/" in out


def test_never_invents_a_price():
    out = pricing.build_pricing_skeleton("Acme", [{"name": "X", "url": "https://acme.com/x"}])
    assert "{{fill in" in out
    # no digit anywhere that could look like a fabricated price
    assert not any(c.isdigit() for c in out.replace("acme.com/x", ""))


def test_empty_money_pages_still_has_title():
    out = pricing.build_pricing_skeleton("Acme", [])
    assert out.startswith("# Pricing - Acme")
    assert "No money_pages" in out


def test_falls_back_to_url_when_name_missing():
    out = pricing.build_pricing_skeleton("Acme", [{"url": "https://acme.com/x"}])
    assert "## https://acme.com/x" in out
