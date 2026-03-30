import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.feature_cache import feature_cache
else:
    from programs.feature_cache import feature_cache


def test_missing_key_returns_none():
    """A key that was never stored should yield None."""
    cache = {}
    result = feature_cache(cache, "user:features:42", 1000.0)
    assert result is None


def test_valid_entry_well_before_expiry():
    """An entry looked up well before its TTL should return the payload."""
    cache = {"model:v3": ({"weight": 0.75}, 2000.0)}
    result = feature_cache(cache, "model:v3", 1500.0)
    assert result == {"weight": 0.75}


def test_expired_entry_returns_none():
    """An entry whose TTL is strictly in the past should not be served."""
    cache = {"flags:dark_launch": (True, 500.0)}
    result = feature_cache(cache, "flags:dark_launch", 600.0)
    assert result is None


def test_negative_timestamp_raises():
    """Negative timestamps are invalid and must raise ValueError."""
    cache = {"k": ("data", 100.0)}
    with pytest.raises(ValueError):
        feature_cache(cache, "k", -1.0)


def test_payload_string_type():
    """String payloads must be returned verbatim when valid."""
    cache = {"banner:text": ("Welcome back!", 9999.0)}
    result = feature_cache(cache, "banner:text", 100.0)
    assert result == "Welcome back!"


def test_exact_ttl_boundary_returns_none():
    """When the current time equals the TTL exactly, the entry should be considered expired."""
    cache = {"session:token": ("abc123", 1000.0)}
    result = feature_cache(cache, "session:token", 1000.0)
    assert result is None


def test_one_tick_before_ttl_still_valid():
    """An entry checked one unit before its TTL should still be served."""
    cache = {"rate:config": ({"limit": 100}, 1000.0)}
    result = feature_cache(cache, "rate:config", 999.0)
    assert result == {"limit": 100}


def test_integer_ttl_exact_match():
    """Integer TTL values at the boundary must expire the entry."""
    cache = {"feature:toggle": (True, 500)}
    result = feature_cache(cache, "feature:toggle", 500)
    assert result is None


def test_multiple_keys_independent_expiry():
    """Each key should be evaluated against its own TTL independently."""
    cache = {
        "a": ("alpha", 100.0),
        "b": ("beta", 200.0),
    }
    assert feature_cache(cache, "a", 100.0) is None
    assert feature_cache(cache, "b", 100.0) == "beta"


def test_zero_timestamp_with_future_ttl():
    """A lookup at time zero should return entries whose TTL is in the future."""
    cache = {"init:payload": ([1, 2, 3], 1.0)}
    result = feature_cache(cache, "init:payload", 0.0)
    assert result == [1, 2, 3]
