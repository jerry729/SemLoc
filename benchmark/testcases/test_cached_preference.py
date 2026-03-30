import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cached_preference import cached_preference
else:
    from programs.cached_preference import cached_preference


def test_cache_miss_returns_none():
    """A missing key should result in None without raising an error."""
    cache = {}
    result = cached_preference(cache, "theme", 1000.0)
    assert result is None


def test_valid_entry_returned_before_expiry():
    """An entry whose TTL has not been reached should be returned."""
    cache = {"locale": ("en_US", 2000.0)}
    result = cached_preference(cache, "locale", 1500.0)
    assert result == "en_US"


def test_expired_entry_returns_none():
    """An entry well past its TTL should not be returned."""
    cache = {"timezone": ("UTC", 1000.0)}
    result = cached_preference(cache, "timezone", 1500.0)
    assert result is None


def test_invalid_empty_key_raises():
    """An empty or whitespace-only key should raise ValueError."""
    cache = {"x": ("val", 9999.0)}
    with pytest.raises(ValueError):
        cached_preference(cache, "   ", 100.0)


def test_whitespace_padded_key_matches_stripped():
    """Leading/trailing whitespace in the key should be stripped before lookup."""
    cache = {"font_size": (14, 5000.0)}
    result = cached_preference(cache, "  font_size  ", 1000.0)
    assert result == 14


def test_entry_at_exact_ttl_boundary_is_expired():
    """When current time equals the TTL exactly, the entry should be considered expired."""
    cache = {"color": ("#FF0000", 1000.0)}
    result = cached_preference(cache, "color", 1000.0)
    assert result is None


def test_entry_one_tick_before_ttl_is_valid():
    """An entry accessed one microsecond before its TTL should still be valid."""
    cache = {"lang": ("de", 1000.0)}
    result = cached_preference(cache, "lang", 999.999999)
    assert result == "de"


def test_integer_ttl_at_exact_boundary():
    """Integer timestamps at the exact expiry boundary should expire the entry."""
    cache = {"mode": ("dark", 500)}
    result = cached_preference(cache, "mode", 500)
    assert result is None


def test_payload_with_complex_structure():
    """The cache should correctly return dict payloads when the entry is fresh."""
    payload = {"notifications": True, "volume": 0.8}
    cache = {"settings": (payload, 9999.0)}
    result = cached_preference(cache, "settings", 5000.0)
    assert result == payload


def test_multiple_keys_independent_expiry():
    """Each key's TTL should be evaluated independently; one expired key should not affect another."""
    cache = {
        "a": ("alpha", 100.0),
        "b": ("beta", 500.0),
    }
    assert cached_preference(cache, "a", 200.0) is None
    assert cached_preference(cache, "b", 200.0) == "beta"
