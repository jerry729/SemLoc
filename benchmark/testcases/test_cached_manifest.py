import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cached_manifest import cached_manifest
else:
    from programs.cached_manifest import cached_manifest


def test_cache_hit_well_before_expiry():
    """A lookup well before the expiry timestamp should return the cached value."""
    entries = {"pkg/v1": ("manifest_data_v1", 1000.0)}
    result = cached_manifest(entries, "pkg/v1", 500.0)
    assert result == "manifest_data_v1"


def test_cache_miss_for_unknown_key():
    """Looking up a key that was never stored should return None."""
    entries = {"pkg/v1": ("manifest_data_v1", 1000.0)}
    result = cached_manifest(entries, "pkg/v2", 500.0)
    assert result is None


def test_expired_entry_returns_none():
    """An entry whose expiry is strictly in the past should not be served."""
    entries = {"pkg/v1": ("manifest_data_v1", 1000.0)}
    result = cached_manifest(entries, "pkg/v1", 1500.0)
    assert result is None


def test_empty_cache_returns_none():
    """Querying an empty manifest cache should always return None."""
    result = cached_manifest({}, "any_key", 100.0)
    assert result is None


def test_entry_exactly_at_expiry_boundary():
    """When the current time equals the expiry, the entry should be considered expired."""
    entries = {"release/2.0": ({"files": ["a.whl"]}, 2000.0)}
    result = cached_manifest(entries, "release/2.0", 2000.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry queried one microsecond before expiry should still be valid."""
    entries = {"release/2.0": ({"files": ["a.whl"]}, 2000.0)}
    result = cached_manifest(entries, "release/2.0", 1999.999999)
    assert result == {"files": ["a.whl"]}


def test_multiple_keys_independent_expiry():
    """Each cache key should be evaluated against its own expiry timestamp."""
    entries = {
        "alpha": ("data_alpha", 100.0),
        "beta": ("data_beta", 200.0),
    }
    assert cached_manifest(entries, "alpha", 150.0) is None
    assert cached_manifest(entries, "beta", 150.0) == "data_beta"


def test_integer_timestamps_at_boundary():
    """Integer timestamps at the exact expiry second should be treated as expired."""
    entries = {"cfg": ("config_snapshot", 500)}
    result = cached_manifest(entries, "cfg", 500)
    assert result is None


def test_value_is_none_but_entry_valid():
    """A cached value of None should be distinguishable from a cache miss only by existence."""
    entries = {"nullable": (None, 9999.0)}
    result = cached_manifest(entries, "nullable", 1.0)
    assert result is None


def test_large_cache_within_limit():
    """A cache with many entries below the limit should function normally."""
    entries = {f"key_{i}": (f"val_{i}", 5000.0) for i in range(4000)}
    assert cached_manifest(entries, "key_0", 1000.0) == "val_0"
    assert cached_manifest(entries, "key_3999", 6000.0) is None
