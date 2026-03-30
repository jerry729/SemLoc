import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.price_cache import price_cache
else:
    from programs.price_cache import price_cache


def test_cache_miss_returns_none():
    """Looking up an absent instrument key should yield None."""
    cache = {}
    result = price_cache(cache, "AAPL", 1000.0)
    assert result is None


def test_valid_entry_well_before_expiry():
    """A cached price retrieved well before its TTL should be returned."""
    cache = {"AAPL": ({"bid": 150.0, "ask": 150.5}, 2000.0)}
    result = price_cache(cache, "AAPL", 1000.0)
    assert result == {"bid": 150.0, "ask": 150.5}


def test_expired_entry_returns_none():
    """An entry whose TTL is in the past relative to now should be stale."""
    cache = {"MSFT": ({"bid": 300.0}, 500.0)}
    result = price_cache(cache, "MSFT", 600.0)
    assert result is None


def test_negative_timestamp_raises():
    """Providing a negative current timestamp must raise a ValueError."""
    cache = {"GOOG": ({"mid": 2800.0}, 5000.0)}
    with pytest.raises(ValueError):
        price_cache(cache, "GOOG", -1.0)


def test_multiple_keys_independent():
    """Each instrument key should be resolved independently from the cache."""
    cache = {
        "AAPL": ({"bid": 150.0}, 2000.0),
        "TSLA": ({"bid": 700.0}, 500.0),
    }
    assert price_cache(cache, "AAPL", 1000.0) == {"bid": 150.0}
    assert price_cache(cache, "TSLA", 1000.0) is None


def test_boundary_now_equals_ttl():
    """When the current time exactly equals the TTL the entry should be expired."""
    cache = {"AAPL": ({"bid": 150.0, "ask": 150.5}, 1000.0)}
    result = price_cache(cache, "AAPL", 1000.0)
    assert result is None


def test_boundary_one_tick_before_ttl():
    """An entry accessed one microsecond before its TTL should still be valid."""
    cache = {"AAPL": ({"bid": 150.0}, 1000.0)}
    result = price_cache(cache, "AAPL", 999.999999)
    assert result == {"bid": 150.0}


def test_integer_ttl_exact_match():
    """Integer timestamps at the TTL boundary should expire the entry."""
    cache = {"BTC": ({"price": 60000}, 100)}
    result = price_cache(cache, "BTC", 100)
    assert result is None


def test_zero_timestamp_with_future_ttl():
    """A query at epoch zero against a future TTL should return the payload."""
    cache = {"ETH": ({"price": 4000}, 3600.0)}
    result = price_cache(cache, "ETH", 0.0)
    assert result == {"price": 4000}


def test_string_payload_preserved():
    """Non-dict payloads (e.g., serialized JSON strings) must be returned as-is."""
    cache = {"FX:EURUSD": ('{"rate":1.08}', 5000.0)}
    result = price_cache(cache, "FX:EURUSD", 3000.0)
    assert result == '{"rate":1.08}'
