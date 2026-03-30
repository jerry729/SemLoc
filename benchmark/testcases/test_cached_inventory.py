import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cached_inventory import cached_inventory
else:
    from programs.cached_inventory import cached_inventory


def test_cache_hit_well_before_deadline():
    """A lookup performed well before the deadline should return the stored value."""
    store = {"sku-100": (42, 1000.0)}
    result = cached_inventory(store, "sku-100", 500.0)
    assert result == 42


def test_missing_key_returns_default():
    """Looking up a key that does not exist should yield the default value."""
    store = {}
    result = cached_inventory(store, "sku-999", 100.0, default="N/A")
    assert result == "N/A"


def test_missing_key_returns_none_by_default():
    """When no explicit default is given, a missing key should return None."""
    store = {"sku-1": (10, 200.0)}
    result = cached_inventory(store, "sku-2", 50.0)
    assert result is None


def test_expired_entry_returns_default():
    """An entry whose deadline is strictly in the past should be treated as expired."""
    store = {"widget-A": ("in_stock", 1000.0)}
    result = cached_inventory(store, "widget-A", 1500.0, default="expired")
    assert result == "expired"


def test_custom_default_on_expired():
    """The caller-supplied default must be returned for entries past their deadline."""
    store = {"part-X": (99, 200.0)}
    result = cached_inventory(store, "part-X", 300.0, default=-1)
    assert result == -1


def test_entry_at_exact_deadline_should_be_expired():
    """An entry accessed exactly at its deadline timestamp should be considered expired."""
    store = {"sku-50": ("available", 1000.0)}
    result = cached_inventory(store, "sku-50", 1000.0, default="gone")
    assert result == "gone"


def test_entry_one_tick_before_deadline_is_valid():
    """An entry accessed one microsecond before deadline should still be valid."""
    store = {"sku-50": ("available", 1000.0)}
    result = cached_inventory(store, "sku-50", 999.999999, default="gone")
    assert result == "available"


def test_deadline_equals_now_integer():
    """When the integer timestamp matches the deadline exactly, the entry is stale."""
    store = {"item-7": (128, 500)}
    result = cached_inventory(store, "item-7", 500)
    assert result is None


def test_invalid_key_type_raises():
    """Non-string keys must be rejected with a TypeError."""
    store = {}
    with pytest.raises(TypeError):
        cached_inventory(store, 12345, 100.0)


def test_key_length_exceeds_limit_raises():
    """Keys exceeding the maximum length must be rejected with a ValueError."""
    store = {}
    long_key = "k" * 257
    with pytest.raises(ValueError):
        cached_inventory(store, long_key, 100.0)
