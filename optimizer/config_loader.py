#!/usr/bin/env python3
"""
Shared config loader. Reads config.json from the project root so every script
pulls brand, domain and URL patterns from one place. No brand name is hard-coded
anywhere else.

config.json is gitignored (it holds your real brand). The committed template is
config.example.json: copy it to config.json and edit. If config.json is missing,
the loader falls back to config.example.json and prints a one-line hint to stderr.
"""
import json
import os
import sys

# Windows consoles/pipes default to cp1252, so printing a heading or URL containing a
# non-latin character would raise UnicodeEncodeError mid-report. Every script imports
# this module, so make stdout/stderr UTF-8 here once.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

_DEFAULTS = {
    "brand_name": "Your Brand",
    "domain": "example.com",
    "base_url": "https://www.example.com/",
    "info_path": "info",
    "blog_path": "blog",
    "money_page_pattern": "https://www.example.com/{slug}/",
    "max_brand_mentions": 1,
    "course_keyword_map": {},
    "country_slugs": [],
    # Optional: override the oldest stat/freshness year accepted by qa_check.py
    # (Rule 12). null = rolling default (current year minus 2, see constants.py).
    "min_stat_year": None,
}


def project_root():
    # optimizer/ sits one level under the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def config_path():
    """Path to the config file. The SEO_GEO_CONFIG env var overrides the default
    (project-root config.json) so tests can pin a fixed config independent of whatever
    brand config.json currently holds."""
    override = os.environ.get("SEO_GEO_CONFIG")
    if override:
        return override
    return os.path.join(project_root(), "config.json")


def example_config_path():
    """Path to the committed, brand-neutral template (config.example.json)."""
    return os.path.join(project_root(), "config.example.json")


# Expected type per key. A mismatch (e.g. country_slugs given as a string instead of
# a list) would otherwise fail silently deep inside a script - iterating characters
# instead of raising - so validate against the shape, not just presence.
_EXPECTED_TYPES = {
    "brand_name": str,
    "domain": str,
    "base_url": str,
    "info_path": str,
    "blog_path": str,
    "money_page_pattern": str,
    "max_brand_mentions": int,
    "course_keyword_map": dict,
    "country_slugs": list,
}


class ConfigError(ValueError):
    pass


def _validate(cfg, path):
    for key, expected in _EXPECTED_TYPES.items():
        val = cfg.get(key)
        # isinstance(True, int) is True in Python, which would let a typo'd
        # "max_brand_mentions": true slip past this as if it were 1 - so bool is
        # only valid where it's actually expected (nowhere, currently).
        wrong_type = not isinstance(val, expected) or (expected is int and isinstance(val, bool))
        if wrong_type:
            raise ConfigError(
                f"{path}: '{key}' must be a {expected.__name__}, got {type(val).__name__} ({val!r})"
            )
    for key, terms in cfg["course_keyword_map"].items():
        if not isinstance(terms, list) or not all(isinstance(t, str) for t in terms):
            raise ConfigError(
                f"{path}: course_keyword_map['{key}'] must be a list of strings, got {terms!r}"
            )
    for slug in cfg["country_slugs"]:
        if not isinstance(slug, str):
            raise ConfigError(f"{path}: country_slugs entries must be strings, got {slug!r}")
    msy = cfg.get("min_stat_year")
    if msy is not None and (not isinstance(msy, int) or isinstance(msy, bool)):
        raise ConfigError(f"{path}: 'min_stat_year' must be an int or null, got {msy!r}")


def load_config():
    """Return the merged config (config file over defaults). Missing file = defaults."""
    cfg = dict(_DEFAULTS)
    path = config_path()
    if not os.path.exists(path) and not os.environ.get("SEO_GEO_CONFIG"):
        example = example_config_path()
        if os.path.exists(example):
            print(f"NOTE: {path} not found; using {example}. "
                  f"Copy config.example.json to config.json and set your brand.",
                  file=sys.stderr)
            path = example
    if os.path.exists(path):
        # utf-8-sig: a config saved by Windows Notepad starts with a BOM, which
        # plain utf-8 would hand to json.load as a stray character.
        with open(path, encoding="utf-8-sig") as f:
            user = json.load(f)
        for k, v in user.items():
            if not k.startswith("_"):   # ignore _note / _example keys
                cfg[k] = v
    _validate(cfg, path)
    return cfg


CONFIG = load_config()
