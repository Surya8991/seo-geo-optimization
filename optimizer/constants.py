#!/usr/bin/env python3
"""
Shared constants used across the optimizer scripts, kept in one place so the
stop-word list and rule thresholds do not drift between cannibal.py, ledger.py,
and qa_check.py.
"""

# Generic stop words for subtopic tokenizing (cannibal.py, ledger.py).
STOP_WORDS = {
    "the", "a", "an", "of", "for", "to", "in", "and", "or", "how", "what",
    "why", "with", "your", "you", "is", "are", "on", "best", "top", "guide",
}

# Link budget: (max_words, internal_max, external_max). Used by qa_check.py.
LINK_BUDGET = [
    (2000, 4, 3),
    (4000, 7, 4),
    (6000, 9, 5),
    (10 ** 9, 10, 6),
]

# Stats/freshness: content must use data from this year or later (Rule 12).
MIN_STAT_YEAR = 2024

# FAQ count band: (max_words, min_faqs, max_faqs). Used by qa_check.py (Rule 11).
FAQ_BAND = [
    (3000, 5, 6),
    (6000, 6, 8),
    (10 ** 9, 8, 10),
]

# Below this many pages, the "whole site" comparisons (cannibalization, duplicate
# meta, striking-distance, next-page ranking, inbound-link discovery) are running
# against too little data to mean anything. Used by meta_audit.py, cannibal.py,
# next.py, interlink.py, striking.py.
SMALL_INVENTORY_THRESHOLD = 5


def small_inventory_warning(n, source="scorecard.json/audit.json"):
    """One-line warning if `n` pages is too small a sample for a site-wide
    comparison to be meaningful, else None. A count of 0 is its own, separate
    "file not found/empty" case and is not warned about here."""
    if 0 < n < SMALL_INVENTORY_THRESHOLD:
        return (f"WARNING: only {n} page(s) loaded from {source} - site-wide "
                f"comparisons are not meaningful until a full GSC + inventory export "
                f"is loaded via build_scorecard.py.")
    return None

# Meta field length gates (qa_check.py).
META_TITLE_MAX = 60
# Google truncates the description around 155-160 chars; a slightly shorter one
# is fine. The band is intentionally not razor-thin so valid copy does not FAIL.
META_DESC_MIN = 140
META_DESC_MAX = 160
