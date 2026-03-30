import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.summary_memo import summary_memo
else:
    from programs.summary_memo import summary_memo


def test_cache_hit_well_before_expiry():
    """A lookup performed well before the expiration time must return the cached value."""
    entries = {"report_daily": (42, 1000.0)}
    result = summary_memo(entries, "report_daily", 500.0)
    assert result == 42


def test_cache_miss_for_absent_key():
    """Looking up a key that has never been cached must return None."""
    entries = {"report_daily": (42, 1000.0)}
    result = summary_memo(entries, "report_weekly", 500.0)
    assert result is None


def test_expired_entry_returns_none():
    """An entry whose expiry is strictly in the past must not be returned."""
    entries = {"metrics_p99": ("value", 100.0)}
    result = summary_memo(entries, "metrics_p99", 200.0)
    assert result is None


def test_empty_cache_returns_none():
    """An empty cache dictionary must always result in a cache miss."""
    result = summary_memo({}, "any_key", 0.0)
    assert result is None


def test_entry_at_exact_expiry_boundary():
    """When the current time equals the expiry timestamp the entry must be treated as expired."""
    entries = {"rollup_hourly": ({"count": 10}, 500.0)}
    result = summary_memo(entries, "rollup_hourly", 500.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one unit before expiration must still be valid."""
    entries = {"rollup_hourly": ({"count": 10}, 500.0)}
    result = summary_memo(entries, "rollup_hourly", 499.0)
    assert result == {"count": 10}


def test_integer_timestamps_at_boundary():
    """Integer timestamps at the exact boundary must respect expiry semantics."""
    entries = {"summary_a": ("hello", 100)}
    assert summary_memo(entries, "summary_a", 100) is None


def test_invalid_empty_key_raises():
    """An empty cache key must be rejected with a ValueError."""
    with pytest.raises(ValueError):
        summary_memo({"x": (1, 100)}, "", 50.0)


def test_stale_marker_in_key_raises():
    """A cache key containing the reserved stale marker must be rejected."""
    with pytest.raises(ValueError):
        summary_memo({}, "prefix__stale__suffix", 50.0)


def test_multiple_entries_independent_expiry():
    """Each entry's expiry must be evaluated independently of other entries."""
    entries = {
        "fast": ("quick", 100.0),
        "slow": ("patient", 9999.0),
    }
    assert summary_memo(entries, "fast", 100.0) is None
    assert summary_memo(entries, "slow", 100.0) == "patient"
