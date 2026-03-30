import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.profile_expiry import profile_expiry
else:
    from programs.profile_expiry import profile_expiry


def test_missing_key_returns_none():
    """Looking up a key that does not exist in the cache must return None."""
    entries = {"alice": ("profile_a", 1000.0)}
    assert profile_expiry(entries, "bob", 500.0) is None


def test_empty_cache_returns_none():
    """An empty cache should always return None for any key."""
    assert profile_expiry({}, "alice", 0.0) is None


def test_valid_entry_before_expiry():
    """A cached profile accessed well before its expiry should be returned."""
    entries = {"user42": ({"name": "Ada"}, 2000.0)}
    result = profile_expiry(entries, "user42", 1500.0)
    assert result == {"name": "Ada"}


def test_expired_entry_long_past():
    """A profile whose expiry is far in the past must not be served."""
    entries = {"user42": ("stale_data", 1000.0)}
    assert profile_expiry(entries, "user42", 5000.0) is None


def test_entry_at_exact_expiry_boundary():
    """When the current time equals the expiry, the entry should be considered expired."""
    entries = {"session": ("payload", 100.0)}
    result = profile_expiry(entries, "session", 100.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one microsecond before expiry should still be valid."""
    entries = {"session": ("payload", 100.0)}
    result = profile_expiry(entries, "session", 99.999999)
    assert result == "payload"


def test_integer_timestamps_at_boundary():
    """Integer timestamp equal to expiry must cause the entry to be treated as expired."""
    entries = {"k": (42, 500)}
    assert profile_expiry(entries, "k", 500) is None


def test_zero_expiry_accessed_at_zero():
    """An entry that expires at time 0 accessed at time 0 is expired."""
    entries = {"ephemeral": ("data", 0.0)}
    assert profile_expiry(entries, "ephemeral", 0.0) is None


def test_negative_expiry_raises():
    """Entries with a negative expiry timestamp should raise ValueError."""
    entries = {"bad": ("x", -10.0)}
    with pytest.raises(ValueError):
        profile_expiry(entries, "bad", 5.0)


def test_multiple_entries_independent():
    """Expiry checks for one key must not affect another key's result."""
    entries = {
        "fresh": ("ok", 9999.0),
        "stale": ("old", 10.0),
    }
    assert profile_expiry(entries, "fresh", 50.0) == "ok"
    assert profile_expiry(entries, "stale", 50.0) is None
