import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cacheline_expiry import cacheline_expiry
else:
    from programs.cacheline_expiry import cacheline_expiry


def test_cache_miss_returns_none():
    """A missing key should yield None regardless of the timestamp."""
    cache = {}
    assert cacheline_expiry(cache, "session:abc", 1000.0) is None


def test_valid_entry_before_expiry():
    """A payload should be returned when the current time is well before the TTL."""
    cache = {"token:xyz": ({"user": "alice"}, 2000.0)}
    result = cacheline_expiry(cache, "token:xyz", 1500.0)
    assert result == {"user": "alice"}


def test_expired_entry_after_ttl():
    """An entry whose TTL is strictly in the past should not be returned."""
    cache = {"rate:api": (42, 1000.0)}
    result = cacheline_expiry(cache, "rate:api", 1500.0)
    assert result is None


def test_negative_timestamp_raises():
    """Negative timestamps are invalid and should raise ValueError."""
    cache = {"k": ("v", 100.0)}
    with pytest.raises(ValueError):
        cacheline_expiry(cache, "k", -1.0)


def test_entry_with_zero_ttl_at_zero_now():
    """An entry expiring at t=0 queried at t=0 should be considered expired."""
    cache = {"early": ("data", 0.0)}
    result = cacheline_expiry(cache, "early", 0.0)
    assert result is None


def test_exact_ttl_boundary_should_expire():
    """When the current time equals the TTL exactly, the entry should be expired."""
    cache = {"boundary": ("secret", 5000.0)}
    result = cacheline_expiry(cache, "boundary", 5000.0)
    assert result is None


def test_one_tick_before_ttl_returns_payload():
    """An entry queried one unit before its TTL should still be valid."""
    cache = {"fresh": ([1, 2, 3], 100.0)}
    result = cacheline_expiry(cache, "fresh", 99.0)
    assert result == [1, 2, 3]


def test_integer_ttl_at_boundary():
    """Integer timestamps at the exact boundary should mark the entry as expired."""
    cache = {"count": (999, 300)}
    result = cacheline_expiry(cache, "count", 300)
    assert result is None


def test_multiple_keys_independent_expiry():
    """Each cache key should be evaluated independently for expiry."""
    cache = {
        "a": ("alpha", 100.0),
        "b": ("beta", 200.0),
    }
    assert cacheline_expiry(cache, "a", 150.0) is None
    assert cacheline_expiry(cache, "b", 150.0) == "beta"


def test_large_payload_retrieval():
    """Large payloads should be returned intact when the entry is valid."""
    big_payload = list(range(10000))
    cache = {"big": (big_payload, 99999.0)}
    result = cacheline_expiry(cache, "big", 50000.0)
    assert result == big_payload
