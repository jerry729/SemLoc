import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.draft_cache import draft_cache
else:
    from programs.draft_cache import draft_cache


def test_missing_key_returns_none():
    """Looking up a key that was never cached must return None."""
    entries = {"alpha": ("doc_v1", 1000.0)}
    assert draft_cache(entries, "beta", 500.0) is None


def test_valid_entry_well_before_expiration():
    """A cached draft retrieved well before its expiration should be returned."""
    entries = {"report": ("draft_body", 2000.0)}
    result = draft_cache(entries, "report", 1500.0)
    assert result == "draft_body"


def test_expired_entry_returns_none():
    """A draft whose expiration is in the past must not be served."""
    entries = {"invoice": ({"total": 99.50}, 1000.0)}
    result = draft_cache(entries, "invoice", 1500.0)
    assert result is None


def test_empty_cache_returns_none():
    """An empty cache should always return None regardless of key."""
    assert draft_cache({}, "anything", 0.0) is None


def test_multiple_entries_independent():
    """Each cache entry is independent; reading one does not affect another."""
    entries = {
        "a": ("val_a", 500.0),
        "b": ("val_b", 1500.0),
    }
    assert draft_cache(entries, "a", 600.0) is None
    assert draft_cache(entries, "b", 600.0) == "val_b"


def test_entry_at_exact_expiration_boundary():
    """When the current time exactly equals the expiration timestamp the entry must be considered expired."""
    entries = {"session": ("user_data", 1000.0)}
    result = draft_cache(entries, "session", 1000.0)
    assert result is None


def test_entry_one_tick_before_expiration():
    """An entry accessed one microsecond before expiration should still be valid."""
    entries = {"token": ("abc123", 1000.0)}
    result = draft_cache(entries, "token", 999.999999)
    assert result == "abc123"


def test_zero_expiration_queried_at_zero():
    """An entry with expiration 0.0 queried at time 0.0 should be treated as expired."""
    entries = {"ephemeral": ("data", 0.0)}
    result = draft_cache(entries, "ephemeral", 0.0)
    assert result is None


def test_integer_timestamps_at_boundary():
    """Integer timestamps at the exact expiration boundary should be treated as expired."""
    entries = {"config": ({"retries": 3}, 500)}
    result = draft_cache(entries, "config", 500)
    assert result is None


def test_malformed_entry_raises_value_error():
    """A cache entry that is not a valid 2-tuple must raise ValueError."""
    entries = {"bad": [1, 2, 3]}
    with pytest.raises(ValueError):
        draft_cache(entries, "bad", 100.0)
