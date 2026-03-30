import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.cached_metric import cached_metric
else:
    from programs.cached_metric import cached_metric


def test_missing_key_returns_none():
    """A cache miss for a non-existent key should yield None."""
    cache = {"cpu_usage": ({"value": 42}, 1000.0)}
    result = cached_metric(cache, "disk_io", 500.0)
    assert result is None


def test_empty_cache_returns_none():
    """An empty cache should always return None regardless of key."""
    result = cached_metric({}, "any_key", 100.0)
    assert result is None


def test_valid_hit_well_before_expiry():
    """A lookup well before the TTL should return the stored payload."""
    payload = {"metric": "latency", "p99": 12.5}
    cache = {"latency": (payload, 2000.0)}
    result = cached_metric(cache, "latency", 1000.0)
    assert result == payload


def test_expired_entry_returns_none():
    """An entry whose TTL is strictly in the past should not be served."""
    cache = {"cpu": ({"value": 85}, 500.0)}
    result = cached_metric(cache, "cpu", 600.0)
    assert result is None


def test_negative_timestamp_raises():
    """The system must reject negative timestamps as invalid."""
    cache = {"k": ("data", 100.0)}
    with pytest.raises(ValueError):
        cached_metric(cache, "k", -1.0)


def test_non_numeric_timestamp_raises():
    """The system must reject non-numeric timestamp arguments."""
    cache = {"k": ("data", 100.0)}
    with pytest.raises(TypeError):
        cached_metric(cache, "k", "now")


def test_exact_ttl_boundary_returns_none():
    """When the current time equals the TTL exactly, the entry is expired."""
    payload = {"requests": 150}
    cache = {"rps": (payload, 1000.0)}
    result = cached_metric(cache, "rps", 1000.0)
    assert result is None


def test_one_tick_before_expiry_returns_payload():
    """An entry accessed one unit before its TTL should still be valid."""
    payload = {"errors": 3}
    cache = {"error_rate": (payload, 1000.0)}
    result = cached_metric(cache, "error_rate", 999.0)
    assert result == payload


def test_integer_ttl_boundary():
    """Integer timestamps at the exact expiry boundary should expire."""
    cache = {"mem": ({"usage_mb": 1024}, 300)}
    result = cached_metric(cache, "mem", 300)
    assert result is None


def test_zero_ttl_at_zero_now():
    """A TTL of zero with current time zero means the entry is expired."""
    cache = {"boot": ("startup_data", 0.0)}
    result = cached_metric(cache, "boot", 0.0)
    assert result is None
