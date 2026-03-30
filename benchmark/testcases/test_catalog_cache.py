import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.catalog_cache import catalog_cache
else:
    from programs.catalog_cache import catalog_cache


def test_missing_key_returns_none():
    """A lookup for a key that does not exist in the cache must return None."""
    entries = {"product_a": ("data_a", 1000.0)}
    result = catalog_cache(entries, "nonexistent_key", 500.0)
    assert result is None


def test_valid_entry_well_before_expiry():
    """An entry accessed well before its expiration should be returned."""
    entries = {"sku_100": ({"name": "Widget", "price": 9.99}, 2000.0)}
    result = catalog_cache(entries, "sku_100", 1500.0)
    assert result == {"name": "Widget", "price": 9.99}


def test_expired_entry_returns_none():
    """An entry whose expiration time is strictly in the past should not be served."""
    entries = {"item_x": ("stale_data", 100.0)}
    result = catalog_cache(entries, "item_x", 200.0)
    assert result is None


def test_empty_cache_returns_none():
    """An empty cache should always return None regardless of key."""
    result = catalog_cache({}, "any_key", 0.0)
    assert result is None


def test_entry_at_exact_expiry_boundary():
    """When the current time equals the expiration timestamp, the entry must be considered expired."""
    entries = {"catalog_item": ("boundary_value", 500.0)}
    result = catalog_cache(entries, "catalog_item", 500.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one unit before expiration should still be valid."""
    entries = {"fresh_item": (42, 1000.0)}
    result = catalog_cache(entries, "fresh_item", 999.0)
    assert result == 42


def test_multiple_entries_independent_expiry():
    """Each entry has its own expiration; querying one must not affect others."""
    entries = {
        "key_a": ("value_a", 100.0),
        "key_b": ("value_b", 200.0),
    }
    assert catalog_cache(entries, "key_a", 150.0) is None
    assert catalog_cache(entries, "key_b", 150.0) == "value_b"


def test_integer_timestamp_at_expiry():
    """Integer timestamps at the expiry boundary must be treated as expired."""
    entries = {"int_entry": ("payload", 300)}
    result = catalog_cache(entries, "int_entry", 300)
    assert result is None


def test_negative_timestamp_raises():
    """A negative timestamp is invalid and should raise a ValueError."""
    entries = {"k": ("v", 100.0)}
    with pytest.raises(ValueError):
        catalog_cache(entries, "k", -1.0)


def test_non_numeric_timestamp_raises():
    """A non-numeric timestamp must raise a TypeError."""
    entries = {"k": ("v", 100.0)}
    with pytest.raises(TypeError):
        catalog_cache(entries, "k", "not_a_number")
