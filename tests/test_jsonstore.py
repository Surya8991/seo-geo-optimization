"""Tests for the tiny file lock used by ledger.py / verify.py (optimizer/jsonstore.py)."""
import pytest

import jsonstore


def test_lock_is_released_after_use(tmp_path):
    path = str(tmp_path / "store.json")
    with jsonstore.locked(path):
        pass
    with jsonstore.locked(path):
        pass


def test_lock_excludes_concurrent_acquisition(tmp_path):
    path = str(tmp_path / "store.json")
    with jsonstore.locked(path):
        with pytest.raises(jsonstore.LockTimeout):
            with jsonstore.locked(path, timeout=0.2, poll=0.05):
                pass


def test_lock_released_even_if_body_raises(tmp_path):
    path = str(tmp_path / "store.json")
    with pytest.raises(ValueError):
        with jsonstore.locked(path):
            raise ValueError("boom")
    # released despite the exception -> this reacquires immediately, not a timeout
    with jsonstore.locked(path):
        pass
