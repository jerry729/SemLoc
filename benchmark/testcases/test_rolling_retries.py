import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.rolling_retries import rolling_retries
else:
    from programs.rolling_retries import rolling_retries


def test_exact_window_match():
    """When values length equals window, the mean equals the arithmetic average."""
    result = rolling_retries([2.0, 4.0, 6.0], window=3)
    assert abs(result - 4.0) < 1e-9


def test_window_larger_than_values():
    """When fewer values than the window width, the mean should reflect only available data."""
    result = rolling_retries([10.0], window=5)
    assert abs(result - 10.0) < 1e-9


def test_window_smaller_than_values():
    """Only the trailing window elements contribute to the rolling mean."""
    result = rolling_retries([1.0, 2.0, 3.0, 4.0, 5.0], window=3)
    assert abs(result - 4.0) < 1e-9


def test_single_value_default_window():
    """A single observation with the default window should yield that observation."""
    result = rolling_retries([7.0])
    assert abs(result - 7.0) < 1e-9


def test_two_values_window_five():
    """Two samples with a window of five should average the two available samples."""
    result = rolling_retries([3.0, 9.0], window=5)
    assert abs(result - 6.0) < 1e-9


def test_empty_series_raises():
    """An empty retry series is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="empty series"):
        rolling_retries([])


def test_non_positive_window_raises():
    """A zero or negative window is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        rolling_retries([1.0], window=0)


def test_warmup_suppresses_output():
    """If the tail has fewer samples than warmup_min, None is returned."""
    result = rolling_retries([5.0], window=3, warmup_min=5)
    assert result is None


def test_four_values_window_ten():
    """Four observations with a large window should average all four values."""
    result = rolling_retries([2.0, 4.0, 6.0, 8.0], window=10)
    assert abs(result - 5.0) < 1e-9


def test_six_values_window_four():
    """The trailing four of six observations should be averaged correctly."""
    result = rolling_retries([1.0, 1.0, 2.0, 4.0, 6.0, 8.0], window=4)
    assert abs(result - 5.0) < 1e-9
