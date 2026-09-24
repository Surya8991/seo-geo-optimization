#!/usr/bin/env python3
"""
Pure, config-independent scoring/parsing helpers used by build_scorecard.py.

These live here (rather than inline in build_scorecard.py) so they can be imported
and unit-tested without triggering the full export-reading pipeline that runs at
build_scorecard import time.
"""
import re


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def ctr_to_number(val):
    """Parse a raw CTR cell to (number, is_explicit_percent).

    A string like "3.45%" is explicitly a percent. A bare number's scale (fraction
    0-1 vs already-percent) is decided per-column by ctr_column_is_fraction, because
    a single value like 0.8 is ambiguous on its own.
    """
    if val is None:
        return 0.0, False
    if isinstance(val, str):
        s = val.strip()
        explicit_pct = s.endswith("%")
        s = s.rstrip("%").strip()
        try:
            return float(s), explicit_pct
        except ValueError:
            return 0.0, False
    try:
        return float(val), False
    except (ValueError, TypeError):
        return 0.0, False


def ctr_column_is_fraction(raw_numbers):
    """True if a column of bare CTR numbers is fractions (0-1) rather than percents.

    GSC's own xlsx export stores CTR as a fraction (0.0345 = 3.45%). If any value
    exceeds 1.5 the column must already be in percent units, so do not rescale it.
    """
    return all(n <= 1.5 for n in raw_numbers) if raw_numbers else True


def normalise_ctr(raw_numbers):
    """Convenience: given raw bare CTR numbers, return the multiplier to apply (1 or 100)."""
    return 100 if ctr_column_is_fraction(raw_numbers) else 1


def compute_trend(monthly_dict, labels):
    """Percent change between the first and second half of the labeled months."""
    vals = [monthly_dict.get(m, 0) for m in labels]
    if len(vals) < 4:
        return 0.0
    half = len(vals) // 2
    sp, sr = sum(vals[:half]), sum(vals[half:])
    if sp == 0:
        return 100.0 if sr > 0 else 0.0
    return round(((sr - sp) / sp) * 100, 1)


def trend_label(pct):
    return "Rising" if pct > 15 else "Declining" if pct < -15 else "Stable"


def position_band(pos):
    if pos <= 0:
        return "No Data"
    if pos <= 3:
        return "Top 3"
    if pos <= 10:
        return "Page 1 (4-10)"
    if pos <= 20:
        return "Page 2"
    if pos <= 50:
        return "Page 3+"
    return "Deep"


def expected_ctr(pos):
    if pos <= 1:
        return 30.0
    if pos <= 2:
        return 15.0
    if pos <= 3:
        return 10.0
    if pos <= 10:
        return 5.0
    if pos <= 20:
        return 1.5
    return 0.5


def impression_band(imp):
    if imp >= 100000:
        return "Very High"
    if imp >= 10000:
        return "High"
    if imp >= 1000:
        return "Medium"
    if imp >= 100:
        return "Low"
    return "Very Low"


def money_page_pattern_regex(pattern):
    """Turn config.json's {course-slug} money_page_pattern into a matching regex, so
    the money_pages sheet can be validated against the URL shape the operator declared.
    Returns None if the pattern has no placeholder to anchor on.

    A trailing slash is optional on both sides: real exports commonly have one even
    when the configured pattern doesn't (or vice versa), and that alone should not
    make every money page look mismatched.
    """
    if "{course-slug}" not in pattern:
        return None
    escaped = re.escape(pattern.rstrip("/")).replace(re.escape("{course-slug}"), r"[a-z0-9-]+")
    return re.compile(f"^{escaped}/?$", re.I)


def header_index(header_row, names, fallback_idx):
    """Find a column index by header name (case-insensitive) among `names` aliases.

    Returns (index, None) if one of the aliases is present in `header_row`, or
    (fallback_idx, warning_message) if none are - so a reordered export column
    produces a loud warning instead of silently reading the wrong data.
    """
    lower = [str(h).strip().lower() if h else "" for h in header_row]
    for name in names:
        if name in lower:
            return lower.index(name), None
    warning = (f"header {names!r} not found; falling back to column "
               f"{fallback_idx + 1} by position")
    return fallback_idx, warning


def classify_intent(slug, title):
    t = (slug + " " + title).lower()
    if any(s in t for s in ["vs", "versus", "comparison", "best", "top ", "tools",
                            "software", "alternatives", "review"]):
        return "commercial"
    if any(s in t for s in ["login", "portal", "download", "register", "sign up"]):
        return "navigational"
    return "informational"
