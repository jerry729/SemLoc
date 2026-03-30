import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.quote_memo import quote_memo
else:
    from programs.quote_memo import quote_memo


def test_cache_miss_returns_none():
    """Looking up a key not present in the cache should return None."""
    cache = {}
    result = quote_memo(cache, "AAPL:NASDAQ", 1000.0)
    assert result is None


def test_valid_entry_well_before_expiry():
    """An entry accessed well before its TTL should return the payload."""
    cache = {"AAPL:NASDAQ": ({"bid": 150.0, "ask": 150.5}, 2000.0)}
    result = quote_memo(cache, "AAPL:NASDAQ", 1500.0)
    assert result == {"bid": 150.0, "ask": 150.5}


def test_expired_entry_returns_none():
    """An entry accessed after its TTL has fully passed should return None."""
    cache = {"MSFT:NASDAQ": ({"bid": 300.0}, 1000.0)}
    result = quote_memo(cache, "MSFT:NASDAQ", 1001.0)
    assert result is None


def test_negative_timestamp_raises():
    """Providing a negative timestamp is invalid and should raise ValueError."""
    cache = {"GOOG:NASDAQ": ({"bid": 2800.0}, 5000.0)}
    with pytest.raises(ValueError):
        quote_memo(cache, "GOOG:NASDAQ", -1.0)


def test_zero_timestamp_with_future_ttl():
    """A timestamp of zero with a future TTL should return the payload."""
    cache = {"TSLA:NASDAQ": ({"price": 700.0}, 100.0)}
    result = quote_memo(cache, "TSLA:NASDAQ", 0.0)
    assert result == {"price": 700.0}


def test_entry_at_exact_expiry_boundary():
    """When the current time equals the TTL exactly, the entry should be considered expired."""
    cache = {"AAPL:NASDAQ": ({"bid": 150.0, "ask": 150.5}, 1000.0)}
    result = quote_memo(cache, "AAPL:NASDAQ", 1000.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one microsecond before TTL should still be valid."""
    cache = {"AMZN:NASDAQ": ({"bid": 3300.0}, 1000.0)}
    result = quote_memo(cache, "AMZN:NASDAQ", 999.999999)
    assert result == {"bid": 3300.0}


def test_integer_ttl_exact_match():
    """When current time is exactly equal to the integer TTL, the quote should be expired."""
    cache = {"FB:NASDAQ": ("payload_data", 500)}
    result = quote_memo(cache, "FB:NASDAQ", 500)
    assert result is None


def test_string_payload_preserved():
    """The function should faithfully return any payload type, including strings."""
    cache = {"NFLX:NASDAQ": ("raw_quote_string", 2000.0)}
    result = quote_memo(cache, "NFLX:NASDAQ", 1999.0)
    assert result == "raw_quote_string"


def test_multiple_keys_independent_expiry():
    """Each cache key should be evaluated independently for expiry."""
    cache = {
        "A": ({"v": 1}, 100.0),
        "B": ({"v": 2}, 200.0),
    }
    assert quote_memo(cache, "A", 100.0) is None
    assert quote_memo(cache, "B", 100.0) == {"v": 2}
