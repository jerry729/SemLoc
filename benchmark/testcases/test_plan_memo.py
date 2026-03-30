import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_memo import plan_memo
else:
    from programs.plan_memo import plan_memo


def test_missing_key_returns_none():
    """A lookup for a key not present in the cache must return None."""
    entries = {"alpha": ("plan_a", 100.0)}
    assert plan_memo(entries, "beta", 50.0) is None


def test_valid_entry_before_expiry():
    """An entry whose expiry is well in the future should be returned."""
    entries = {"query_plan_1": ("hash_join", 200.0)}
    result = plan_memo(entries, "query_plan_1", 100.0)
    assert result == "hash_join"


def test_expired_entry_returns_none():
    """An entry whose expiry is strictly in the past must not be returned."""
    entries = {"scan_plan": ("seq_scan", 50.0)}
    result = plan_memo(entries, "scan_plan", 100.0)
    assert result is None


def test_empty_cache_returns_none():
    """An empty cache should always yield None regardless of key."""
    assert plan_memo({}, "any_key", 0.0) is None


def test_entry_at_exact_expiry_boundary():
    """When the current time equals the expiry timestamp the entry is no longer valid."""
    entries = {"plan_x": ("nested_loop", 100.0)}
    result = plan_memo(entries, "plan_x", 100.0)
    assert result is None


def test_entry_one_tick_before_expiry():
    """An entry accessed one microsecond before expiry should still be valid."""
    entries = {"plan_y": ("merge_join", 100.0)}
    result = plan_memo(entries, "plan_y", 99.999999)
    assert result == "merge_join"


def test_multiple_entries_independent_expiry():
    """Each entry's expiry is evaluated independently; one expiring does not affect others."""
    entries = {
        "fresh": ("plan_fresh", 200.0),
        "stale": ("plan_stale", 50.0),
    }
    assert plan_memo(entries, "fresh", 100.0) == "plan_fresh"
    assert plan_memo(entries, "stale", 100.0) is None


def test_exact_expiry_integer_timestamps():
    """With integer timestamps, accessing at exactly the expiry second must invalidate."""
    entries = {"job_42": ({"stages": 3}, 300)}
    result = plan_memo(entries, "job_42", 300)
    assert result is None


def test_complex_value_type_preserved():
    """Cached values with complex types should be returned without modification."""
    payload = {"steps": ["scan", "filter", "aggregate"], "cost": 42.5}
    entries = {"analytics_plan": (payload, 1000.0)}
    result = plan_memo(entries, "analytics_plan", 500.0)
    assert result is payload


def test_invalid_entries_type_raises():
    """Passing a non-dict for entries must raise a TypeError."""
    with pytest.raises(TypeError):
        plan_memo(["not", "a", "dict"], "key", 0.0)
