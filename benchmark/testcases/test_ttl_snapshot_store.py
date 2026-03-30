import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.ttl_snapshot_store import ttl_snapshot_store
else:
    from programs.ttl_snapshot_store import ttl_snapshot_store


def test_missing_key_returns_none():
    """A lookup for a key that does not exist must return None."""
    entries = {"alpha": ("data_a", 1000.0)}
    assert ttl_snapshot_store(entries, "beta", 500.0) is None


def test_valid_entry_well_before_expiry():
    """An entry accessed well before its expiry should be returned."""
    entries = {"session": ("tok_abc", 2000.0)}
    result = ttl_snapshot_store(entries, "session", 1000.0)
    assert result == "tok_abc"


def test_expired_entry_returns_none():
    """An entry whose expiry is in the past must not be served."""
    entries = {"session": ("tok_old", 500.0)}
    result = ttl_snapshot_store(entries, "session", 700.0)
    assert result is None


def test_empty_store_returns_none():
    """Querying an empty cache store must always return None."""
    assert ttl_snapshot_store({}, "anything", 100.0) is None


def test_negative_timestamp_raises():
    """Timestamps must be non-negative; a negative value should raise ValueError."""
    with pytest.raises(ValueError):
        ttl_snapshot_store({"k": (1, 10.0)}, "k", -1.0)


def test_exact_expiry_boundary_returns_none():
    """When the current time equals the expiry, the entry should be treated as expired."""
    entries = {"config": ({"retries": 3}, 1500.0)}
    result = ttl_snapshot_store(entries, "config", 1500.0)
    assert result is None


def test_one_tick_before_expiry_returns_value():
    """An entry accessed one unit before its expiry must still be valid."""
    entries = {"metric": (42, 1000.0)}
    result = ttl_snapshot_store(entries, "metric", 999.0)
    assert result == 42


def test_integer_timestamps_at_boundary():
    """Integer timestamps at the exact expiry boundary should invalidate the entry."""
    entries = {"counter": (99, 50)}
    result = ttl_snapshot_store(entries, "counter", 50)
    assert result is None


def test_multiple_keys_independent_expiry():
    """Each key's expiry is independent; only the queried key's TTL matters."""
    entries = {
        "a": ("val_a", 100.0),
        "b": ("val_b", 200.0),
    }
    assert ttl_snapshot_store(entries, "a", 150.0) is None
    assert ttl_snapshot_store(entries, "b", 150.0) == "val_b"


def test_zero_expiry_at_zero_now():
    """An entry with expiry 0 queried at time 0 should be considered expired."""
    entries = {"ephemeral": ("gone", 0.0)}
    result = ttl_snapshot_store(entries, "ephemeral", 0.0)
    assert result is None
