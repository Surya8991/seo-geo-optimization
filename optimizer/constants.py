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

# Meta field length gates (qa_check.py).
META_TITLE_MAX = 60
# Google truncates the description around 155-160 chars; a slightly shorter one
# is fine. The band is intentionally not razor-thin so valid copy does not FAIL.
META_DESC_MIN = 140
META_DESC_MAX = 160
