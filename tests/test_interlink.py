"""Tests for the inbound-link finder (optimizer/interlink.py)."""
import interlink


PAGES = [
    {"slug": "info/agile-scrum-fundamentals", "title": "Agile Scrum Fundamentals",
     "category": "Quick Win"},
    {"slug": "info/scrum-master-salary", "title": "Scrum Master Salary Guide",
     "category": "Performing Well"},
    {"slug": "info/product-certification", "title": "Product Certification Guide",
     "category": "Top Performers Falling"},
    {"slug": "australia", "title": "Training in Australia", "category": "Performing Well"},
]


def test_tokens_drop_stopwords():
    assert interlink.tokens("The best Scrum Master guide") == {"scrum", "master"}


def test_ranks_topically_related_pages():
    target_tokens = {"scrum", "agile", "master"}
    ranked = interlink.rank_inbound(target_tokens, PAGES,
                                    exclude_tail="agile-scrum-fundamentals", country_slugs=[])
    slugs = [p["slug"] for _, _, p in ranked]
    assert "info/scrum-master-salary" in slugs           # shares scrum + master
    assert "info/agile-scrum-fundamentals" not in slugs  # excluded (the target itself)
    assert "info/product-certification" not in slugs      # no topical overlap


def test_country_pages_are_skipped():
    target_tokens = {"training", "scrum"}
    ranked = interlink.rank_inbound(target_tokens, PAGES,
                                    exclude_tail="x", country_slugs=["australia"])
    assert all(p["slug"] != "australia" for _, _, p in ranked)


def test_no_overlap_returns_empty():
    ranked = interlink.rank_inbound({"underwater", "basket"}, PAGES,
                                    exclude_tail="x", country_slugs=[])
    assert ranked == []
