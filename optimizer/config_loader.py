#!/usr/bin/env python3
"""
Shared config loader. Reads config.json from the project root so every script
pulls brand, domain and URL patterns from one place. No brand name is hard-coded
anywhere else.
"""
import json
import os

_DEFAULTS = {
    "brand_name": "Your Brand",
    "domain": "example.com",
    "base_url": "https://www.example.com/",
    "info_path": "info",
    "blog_path": "blog",
    "money_page_pattern": "https://www.example.com/{course-slug}/",
    "max_brand_mentions": 1,
    "course_keyword_map": {},
    "country_slugs": [],
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


def load_config():
    """Return the merged config (config file over defaults). Missing file = defaults."""
    cfg = dict(_DEFAULTS)
    path = config_path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if not k.startswith("_"):   # ignore _note / _example keys
                cfg[k] = v
    _validate(cfg, path)
    return cfg


CONFIG = load_config()
