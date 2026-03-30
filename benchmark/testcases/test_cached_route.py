import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cached_route import cached_route
else:
    from programs.cached_route import cached_route


def test_missing_key_returns_none():
    """A key that was never cached should return None."""
    entries = {"route-alpha": ("/api/v1/alpha", 1000.0)}
    result = cached_route(entries, "route-beta", 500.0)
    assert result is None


def test_valid_entry_well_before_expiry():
    """A route queried well before its expiration should be returned."""
    entries = {"route-alpha": ("/api/v1/alpha", 1000.0)}
    result = cached_route(entries, "route-alpha", 500.0)
    assert result == "/api/v1/alpha"


def test_expired_entry_returns_none():
    """A route whose expiration is strictly in the past should not be served."""
    entries = {"route-alpha": ("/api/v1/alpha", 1000.0)}
    result = cached_route(entries, "route-alpha", 1500.0)
    assert result is None


def test_invalid_key_raises_value_error():
    """An empty string key violates the route-key format and should raise."""
    entries = {"route-alpha": ("/api/v1/alpha", 1000.0)}
    with pytest.raises(ValueError):
        cached_route(entries, "", 500.0)


def test_non_string_key_raises_value_error():
    """Non-string keys should be rejected immediately."""
    entries = {"route-alpha": ("/api/v1/alpha", 1000.0)}
    with pytest.raises(ValueError):
        cached_route(entries, 42, 500.0)


def test_entry_at_exact_expiration_boundary():
    """When the current time equals the expiration time the entry should be treated as expired."""
    entries = {"route-gamma": ("/api/v2/gamma", 2000.0)}
    result = cached_route(entries, "route-gamma", 2000.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """A route queried one tick before expiry should still be valid."""
    entries = {"route-delta": ("/api/v3/delta", 3000.0)}
    result = cached_route(entries, "route-delta", 2999.999999)
    assert result == "/api/v3/delta"


def test_integer_timestamps_at_boundary():
    """Integer timestamps should be handled identically to floats at expiry boundary."""
    entries = {"route-epsilon": ("/svc/epsilon", 500)}
    result = cached_route(entries, "route-epsilon", 500)
    assert result is None


def test_multiple_entries_independent_expiry():
    """Each route should be evaluated against its own expiry, not others."""
    entries = {
        "route-a": ("/a", 100.0),
        "route-b": ("/b", 200.0),
    }
    assert cached_route(entries, "route-a", 150.0) is None
    assert cached_route(entries, "route-b", 150.0) == "/b"


def test_zero_expiry_with_zero_now():
    """A route that expires at timestamp 0 queried at timestamp 0 should be expired."""
    entries = {"route-z": ("/zero", 0.0)}
    result = cached_route(entries, "route-z", 0.0)
    assert result is None
