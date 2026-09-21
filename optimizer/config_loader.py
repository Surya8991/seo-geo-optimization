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


def load_config():
    """Return the merged config (config.json over defaults). Missing file = defaults."""
    cfg = dict(_DEFAULTS)
    path = os.path.join(project_root(), "config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if not k.startswith("_"):   # ignore _note / _example keys
                cfg[k] = v
    return cfg


CONFIG = load_config()
