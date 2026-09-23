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
    return cfg


CONFIG = load_config()
