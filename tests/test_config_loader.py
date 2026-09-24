"""Tests for config type validation (optimizer/config_loader.py)."""
import json

import pytest

import config_loader


def _write_config(tmp_path, monkeypatch, overrides):
    cfg = dict(config_loader._DEFAULTS)
    cfg.update(overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setenv("SEO_GEO_CONFIG", str(path))


def test_default_config_validates():
    cfg = config_loader.load_config()
    assert cfg["brand_name"]


def test_rejects_string_country_slugs(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, {"country_slugs": "not-a-list"})
    with pytest.raises(config_loader.ConfigError):
        config_loader.load_config()


def test_rejects_non_string_country_slug_entries(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, {"country_slugs": ["india", 42]})
    with pytest.raises(config_loader.ConfigError):
        config_loader.load_config()


def test_rejects_list_course_keyword_map(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, {"course_keyword_map": ["not", "a", "dict"]})
    with pytest.raises(config_loader.ConfigError):
        config_loader.load_config()


def test_rejects_non_list_course_keyword_terms(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, {"course_keyword_map": {"course-a": "not-a-list"}})
    with pytest.raises(config_loader.ConfigError):
        config_loader.load_config()


def test_rejects_bool_for_max_brand_mentions(tmp_path, monkeypatch):
    # isinstance(True, int) is True in Python - a typo'd `true` for `1` must still raise.
    _write_config(tmp_path, monkeypatch, {"max_brand_mentions": True})
    with pytest.raises(config_loader.ConfigError):
        config_loader.load_config()


def test_accepts_int_max_brand_mentions(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, {"max_brand_mentions": 2})
    cfg = config_loader.load_config()
    assert cfg["max_brand_mentions"] == 2
