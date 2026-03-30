import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cache_entry_ttl import cache_entry_ttl
else:
    from programs.cache_entry_ttl import cache_entry_ttl


def test_cache_hit_well_before_expiry():
    """An entry accessed well before its expiration time should be returned."""
    store = {"session:abc": ("user_data_payload", 1000.0)}
    result = cache_entry_ttl(store, "session:abc", 500.0)
    assert result == "user_data_payload"


def test_cache_miss_for_absent_key():
    """Looking up a key that was never stored should return None."""
    store = {"session:abc": ("payload", 1000.0)}
    result = cache_entry_ttl(store, "session:xyz", 500.0)
    assert result is None


def test_expired_entry_returns_none():
    """An entry whose expiration time is in the past should not be returned."""
    store = {"token:x": ("secret", 100.0)}
    result = cache_entry_ttl(store, "token:x", 200.0)
    assert result is None


def test_empty_cache_returns_none():
    """Querying an empty cache store should always return None."""
    result = cache_entry_ttl({}, "anything", 0.0)
    assert result is None


def test_entry_at_exact_expiration_boundary():
    """When the current time equals the expiry timestamp, the entry should be
    considered expired and not returned."""
    store = {"rate:limit": (42, 500.0)}
    result = cache_entry_ttl(store, "rate:limit", 500.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one microsecond before its expiry should still be valid."""
    store = {"config:v2": ({"retries": 3}, 1000.0)}
    result = cache_entry_ttl(store, "config:v2", 999.999999)
    assert result == {"retries": 3}


def test_multiple_entries_independent_expiry():
    """Each cache entry should be evaluated against its own expiry, not others."""
    store = {
        "a": ("val_a", 100.0),
        "b": ("val_b", 200.0),
    }
    assert cache_entry_ttl(store, "a", 150.0) is None
    assert cache_entry_ttl(store, "b", 150.0) == "val_b"


def test_integer_expiry_exact_match():
    """Integer timestamps at the exact boundary should be treated as expired."""
    store = {"k": ("v", 10)}
    result = cache_entry_ttl(store, "k", 10)
    assert result is None


def test_zero_ttl_entry_immediately_expires():
    """An entry with expiry at time zero should be expired at time zero."""
    store = {"ephemeral": ("data", 0.0)}
    result = cache_entry_ttl(store, "ephemeral", 0.0)
    assert result is None


def test_value_types_preserved():
    """The cache should faithfully return complex value types without modification."""
    complex_value = {"nested": [1, 2, 3], "flag": True}
    store = {"complex": (complex_value, 9999.0)}
    result = cache_entry_ttl(store, "complex", 1.0)
    assert result == complex_value
    assert result is complex_value
