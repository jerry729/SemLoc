import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.rolling_requests import rolling_requests
else:
    from programs.rolling_requests import rolling_requests


def test_full_window_uniform_traffic():
    """Average of uniform request counts should equal the constant value."""
    result = rolling_requests([100, 100, 100, 100, 100], window=5)
    assert abs(result - 100.0) < 1e-9


def test_full_window_varying_traffic():
    """Average over a full window of varied counts should be arithmetic mean."""
    result = rolling_requests([10, 20, 30, 40, 50], window=5)
    assert abs(result - 30.0) < 1e-9


def test_invalid_window_raises():
    """Non-positive window sizes are invalid for rate computation."""
    with pytest.raises(ValueError, match="invalid window"):
        rolling_requests([1, 2, 3], window=0)


def test_empty_series_raises():
    """An empty sample series cannot produce a rate estimate."""
    with pytest.raises(ValueError, match="no samples"):
        rolling_requests([], window=3)


def test_warmup_returns_none():
    """Before warmup threshold is met the function should withhold results."""
    result = rolling_requests([42], window=5, warmup_min=2)
    assert result is None


def test_fewer_samples_than_window_returns_correct_average():
    """When fewer samples exist than the window, use all available samples."""
    result = rolling_requests([10, 30], window=5, warmup_min=2)
    assert abs(result - 20.0) < 1e-9


def test_three_samples_window_ten():
    """With 3 samples and window=10, the average should reflect those 3 values."""
    result = rolling_requests([6, 12, 18], window=10, warmup_min=2)
    assert abs(result - 12.0) < 1e-9


def test_single_sample_large_window():
    """A single sample within a large window should average to that sample value."""
    result = rolling_requests([50], window=100, warmup_min=1)
    assert abs(result - 50.0) < 1e-9


def test_window_smaller_than_series_uses_tail():
    """Only the trailing window of samples should be considered."""
    result = rolling_requests([1000, 1000, 10, 20, 30], window=3)
    assert abs(result - 20.0) < 1e-9


def test_exact_window_match():
    """When series length equals window, all samples contribute equally."""
    result = rolling_requests([5, 15, 25], window=3, warmup_min=3)
    assert abs(result - 15.0) < 1e-9
