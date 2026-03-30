import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cacheline_refresh import cacheline_refresh
else:
    from programs.cacheline_refresh import cacheline_refresh


def test_missing_key_returns_none():
    """A lookup for a key not present in the store must return None."""
    store = {}
    result = cacheline_refresh(store, "session:abc", now=1000.0)
    assert result is None


def test_expired_entry_returns_none():
    """An entry whose expiration is in the past must not be served."""
    store = {"token:x": ("val", 500.0)}
    result = cacheline_refresh(store, "token:x", now=600.0)
    assert result is None


def test_valid_entry_returns_value():
    """A non-expired entry must return its stored value."""
    store = {"user:42": ({"name": "Alice"}, 2000.0)}
    result = cacheline_refresh(store, "user:42", now=1500.0)
    assert result == {"name": "Alice"}


def test_boundary_exact_expiration_returns_none():
    """When now equals expires_at the entry is still valid (not strictly >)."""
    store = {"k": ("v", 1000.0)}
    result = cacheline_refresh(store, "k", now=1000.0)
    assert result == "v"


def test_store_updated_after_refresh():
    """After a successful lookup the store must contain the extended TTL."""
    store = {"cfg:main": ("payload", 2000.0)}
    cacheline_refresh(store, "cfg:main", now=1500.0, ttl=300)
    _, new_expires = store["cfg:main"]
    assert abs(new_expires - 1800.0) < 1e-9


def test_sliding_window_extends_on_repeated_access():
    """Two consecutive accesses must each slide the expiration forward."""
    store = {"rate:ip": (10, 1000.0)}
    cacheline_refresh(store, "rate:ip", now=900.0, ttl=200)
    _, exp_after_first = store["rate:ip"]
    assert abs(exp_after_first - 1100.0) < 1e-9

    cacheline_refresh(store, "rate:ip", now=1050.0, ttl=200)
    _, exp_after_second = store["rate:ip"]
    assert abs(exp_after_second - 1250.0) < 1e-9


def test_custom_ttl_applied_to_store():
    """A custom TTL value must be reflected in the refreshed expiration."""
    store = {"sess:z": ("data", 5000.0)}
    cacheline_refresh(store, "sess:z", now=4000.0, ttl=600)
    _, refreshed_exp = store["sess:z"]
    assert abs(refreshed_exp - 4600.0) < 1e-9


def test_value_unchanged_after_refresh():
    """The stored value must remain identical after an expiration refresh."""
    original_value = [1, 2, 3]
    store = {"list:a": (original_value, 3000.0)}
    cacheline_refresh(store, "list:a", now=2500.0, ttl=120)
    stored_value, _ = store["list:a"]
    assert stored_value is original_value


def test_ttl_clamped_to_minimum():
    """A TTL below the minimum threshold must be clamped to 1 second."""
    store = {"k": ("v", 500.0)}
    cacheline_refresh(store, "k", now=100.0, ttl=-50)
    _, exp = store["k"]
    assert abs(exp - 101.0) < 1e-9


def test_expired_entry_not_modified_in_store():
    """An expired entry must remain untouched in the store after lookup."""
    store = {"old:item": ("stale", 100.0)}
    cacheline_refresh(store, "old:item", now=200.0)
    _, exp = store["old:item"]
    assert abs(exp - 100.0) < 1e-9
