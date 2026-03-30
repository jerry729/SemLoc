import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.prediction_cache import prediction_cache
else:
    from programs.prediction_cache import prediction_cache


def test_cache_hit_well_before_deadline():
    """A prediction fetched well before its deadline should be returned."""
    store = {"model_v2": (0.95, 1000.0)}
    result = prediction_cache(store, "model_v2", 500.0)
    assert result == 0.95


def test_cache_miss_for_absent_key():
    """Querying a key not in the store should return the default."""
    store = {"model_v2": (0.95, 1000.0)}
    result = prediction_cache(store, "model_v3", 500.0)
    assert result is None


def test_cache_miss_returns_custom_default():
    """A missing key should return the caller-supplied default."""
    store = {}
    result = prediction_cache(store, "absent", 100.0, default=-1)
    assert result == -1


def test_expired_entry_returns_default():
    """An entry whose deadline has clearly passed should be treated as expired."""
    store = {"model_v2": (0.95, 1000.0)}
    result = prediction_cache(store, "model_v2", 1500.0)
    assert result is None


def test_expired_entry_returns_custom_default():
    """An expired entry should respect the caller-supplied default value."""
    store = {"model_v2": (0.95, 1000.0)}
    result = prediction_cache(store, "model_v2", 2000.0, default="stale")
    assert result == "stale"


def test_entry_at_exact_deadline_is_expired():
    """When the current time equals the deadline, the entry should be expired."""
    store = {"score": (42, 100.0)}
    result = prediction_cache(store, "score", 100.0)
    assert result is None


def test_entry_one_tick_before_deadline():
    """An entry queried one tick before its deadline should still be valid."""
    store = {"score": (42, 100.0)}
    result = prediction_cache(store, "score", 99.999)
    assert result == 42


def test_integer_deadline_boundary():
    """At the exact integer deadline, the cache entry must be considered expired."""
    store = {"pred": ("yes", 50)}
    result = prediction_cache(store, "pred", 50)
    assert result is None


def test_zero_time_and_positive_deadline():
    """A prediction stored with a future deadline and accessed at time 0 should be returned."""
    store = {"early": (3.14, 10.0)}
    result = prediction_cache(store, "early", 0.0)
    assert abs(result - 3.14) < 1e-9


def test_deadline_drift_raises_error():
    """A deadline unreasonably far in the future should raise ValueError."""
    store = {"drift": (99, 100000.0)}
    with pytest.raises(ValueError):
        prediction_cache(store, "drift", 1.0)
