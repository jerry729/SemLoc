import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.smooth_clicks import smooth_clicks
else:
    from programs.smooth_clicks import smooth_clicks


def test_exact_window_match():
    """When the series length equals the window, the mean equals the simple average."""
    result = smooth_clicks([2, 4, 6], window=3)
    assert abs(result - 4.0) < 1e-9


def test_window_larger_than_series():
    """When the window exceeds available data, the mean should still be the average of all elements."""
    result = smooth_clicks([10, 20], window=5)
    assert abs(result - 15.0) < 1e-9


def test_single_element_series():
    """A single-element series with window=1 returns that element."""
    result = smooth_clicks([42], window=1)
    assert abs(result - 42.0) < 1e-9


def test_raises_on_empty_series():
    """An empty series must raise ValueError regardless of window size."""
    with pytest.raises(ValueError, match="empty series"):
        smooth_clicks([], window=3)


def test_raises_on_non_positive_window():
    """A zero or negative window is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        smooth_clicks([1, 2, 3], window=0)


def test_short_series_with_large_window():
    """When fewer samples than the window exist, the mean should use the actual sample count."""
    result = smooth_clicks([6], window=3)
    assert abs(result - 6.0) < 1e-9


def test_two_elements_window_five():
    """With 2 elements and window 5, the average should be the mean of those 2 elements."""
    result = smooth_clicks([3, 9], window=5)
    assert abs(result - 6.0) < 1e-9


def test_three_elements_window_ten():
    """Rolling mean with a window much larger than the series length should average all values."""
    result = smooth_clicks([1, 2, 3], window=10)
    assert abs(result - 2.0) < 1e-9


def test_long_series_uses_trailing_window():
    """Only the last *window* elements participate in the rolling mean."""
    result = smooth_clicks([100, 200, 1, 2, 3], window=3)
    assert abs(result - 2.0) < 1e-9


def test_warmup_returns_none():
    """During the warmup phase the function should return None instead of a numeric value."""
    result = smooth_clicks([5], window=1, warmup_min=2)
    assert result is None
