import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.config_expiry import config_expiry
else:
    from programs.config_expiry import config_expiry


def test_missing_key_returns_none():
    """A cache lookup for a non-existent key should yield None."""
    entries = {"db_host": ("10.0.0.1", 1000.0)}
    assert config_expiry(entries, "db_port", 500.0) is None


def test_empty_cache_returns_none():
    """An empty cache store should return None for any key."""
    assert config_expiry({}, "service_url", 100.0) is None


def test_valid_entry_before_expiry():
    """An entry accessed well before its expiry should return the cached value."""
    entries = {"timeout": (30, 2000.0)}
    result = config_expiry(entries, "timeout", 1000.0)
    assert result == 30


def test_entry_long_after_expiry():
    """An entry accessed long after its expiry should return None."""
    entries = {"feature_flag": (True, 500.0)}
    result = config_expiry(entries, "feature_flag", 1000.0)
    assert result is None


def test_entry_at_exact_expiry_boundary():
    """When the current time equals the expiry time the entry should be considered expired."""
    entries = {"rate_limit": (100, 500.0)}
    result = config_expiry(entries, "rate_limit", 500.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one tick before expiry should still be valid."""
    entries = {"retries": (3, 500.0)}
    result = config_expiry(entries, "retries", 499.999)
    assert result == 3


def test_zero_ttl_entry_at_creation():
    """An entry whose expiry equals the creation moment should be expired immediately."""
    entries = {"ephemeral": ("value", 0.0)}
    result = config_expiry(entries, "ephemeral", 0.0)
    assert result is None


def test_multiple_entries_independent_expiry():
    """Each entry should be evaluated against its own expiry, not others'."""
    entries = {
        "key_a": ("alpha", 100.0),
        "key_b": ("beta", 200.0),
    }
    assert config_expiry(entries, "key_a", 150.0) is None
    assert config_expiry(entries, "key_b", 150.0) == "beta"


def test_integer_timestamps_at_boundary():
    """Integer-precision timestamps at the exact expiry should be treated as expired."""
    entries = {"conn_pool_size": (10, 3600)}
    result = config_expiry(entries, "conn_pool_size", 3600)
    assert result is None


def test_negative_expiry_raises():
    """A cache entry with a negative expiry timestamp should raise ValueError."""
    entries = {"bad": ("data", -1.0)}
    with pytest.raises(ValueError):
        config_expiry(entries, "bad", 0.0)
