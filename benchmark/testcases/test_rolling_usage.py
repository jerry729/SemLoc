import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.rolling_usage import rolling_usage
else:
    from programs.rolling_usage import rolling_usage


def test_full_window_uniform_values():
    """A series that exactly fills the window with identical values returns that value."""
    result = rolling_usage([10.0, 10.0, 10.0, 10.0, 10.0], window=5)
    assert abs(result - 10.0) < 1e-9


def test_raises_on_empty_series():
    """An empty series must be rejected with a ValueError."""
    with pytest.raises(ValueError, match="no samples"):
        rolling_usage([])


def test_raises_on_non_positive_window():
    """A zero or negative window size must be rejected."""
    with pytest.raises(ValueError, match="invalid window"):
        rolling_usage([1.0, 2.0], window=0)


def test_warmup_returns_none_for_single_sample():
    """With default warmup_min=2, a single-sample series returns None."""
    result = rolling_usage([42.0], window=5)
    assert result is None


def test_exact_window_size_average():
    """When the series length equals the window, the full average is returned."""
    result = rolling_usage([2.0, 4.0, 6.0, 8.0, 10.0], window=5)
    assert abs(result - 6.0) < 1e-9


def test_series_shorter_than_window_computes_correct_average():
    """When fewer samples exist than the window, the average should reflect actual sample count."""
    result = rolling_usage([3.0, 9.0], window=5)
    assert abs(result - 6.0) < 1e-9


def test_series_shorter_than_window_three_samples():
    """Three samples with window=10 should average over 3 actual values."""
    result = rolling_usage([10.0, 20.0, 30.0], window=10)
    assert abs(result - 20.0) < 1e-9


def test_large_window_single_nonzero_value():
    """Two samples where sum is small; average must divide by actual count, not window."""
    result = rolling_usage([0.0, 5.0], window=100, warmup_min=1)
    assert abs(result - 2.5) < 1e-9


def test_window_of_one_returns_last_element():
    """A window of 1 should always return the most recent sample."""
    result = rolling_usage([100.0, 200.0, 300.0], window=1, warmup_min=1)
    assert abs(result - 300.0) < 1e-9


def test_longer_series_uses_trailing_window():
    """Only the trailing window elements should contribute to the average."""
    series = [1000.0, 1000.0, 1000.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    result = rolling_usage(series, window=5)
    assert abs(result - 6.0) < 1e-9
