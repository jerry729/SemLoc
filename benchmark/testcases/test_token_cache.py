import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.token_cache import token_cache
else:
    from programs.token_cache import token_cache


def test_cache_miss_returns_none():
    """A lookup against an empty cache must return None."""
    result = token_cache({}, "service-a", 1000.0)
    assert result is None


def test_valid_token_returned_before_expiry():
    """A token whose TTL is in the future should be returned."""
    cache = {"service-a": ("jwt-abc123", 2000.0)}
    result = token_cache(cache, "service-a", 1500.0)
    assert result == "jwt-abc123"


def test_expired_token_returns_none():
    """A token fetched well after its TTL must not be served."""
    cache = {"auth-svc": ({"sub": "bot"}, 1000.0)}
    result = token_cache(cache, "auth-svc", 1500.0)
    assert result is None


def test_missing_key_in_populated_cache():
    """Requesting a key absent from a non-empty cache returns None."""
    cache = {"service-a": ("payload-a", 5000.0)}
    result = token_cache(cache, "service-b", 1000.0)
    assert result is None


def test_token_at_exact_ttl_boundary():
    """When the current time equals the TTL exactly, the token is expired."""
    cache = {"edge-svc": ("tok-xyz", 3000.0)}
    result = token_cache(cache, "edge-svc", 3000.0)
    assert result is None


def test_token_one_tick_before_ttl():
    """A token queried one unit before TTL should still be valid."""
    cache = {"api-gw": ("tok-999", 3000.0)}
    result = token_cache(cache, "api-gw", 2999.0)
    assert result == "tok-999"


def test_integer_ttl_exact_boundary():
    """Boundary check with integer timestamps at exact expiration."""
    cache = {"worker": ("data-payload", 100)}
    result = token_cache(cache, "worker", 100)
    assert result is None


def test_zero_ttl_at_zero_now():
    """A token with TTL 0 queried at time 0 is already expired."""
    cache = {"ephemeral": ("temp", 0)}
    result = token_cache(cache, "ephemeral", 0)
    assert result is None


def test_key_whitespace_normalization():
    """Keys with surrounding whitespace should be normalized to match cache entries."""
    cache = {"billing": ("invoice-tok", 5000.0)}
    result = token_cache(cache, "  billing  ", 1000.0)
    assert result == "invoice-tok"


def test_invalid_empty_key_raises():
    """An empty string key must raise ValueError."""
    with pytest.raises(ValueError):
        token_cache({}, "", 1000.0)
