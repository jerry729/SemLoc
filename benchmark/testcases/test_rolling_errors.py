import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.rolling_errors import rolling_errors
else:
    from programs.rolling_errors import rolling_errors


def test_exact_window_match():
    """When the number of values equals the window, the mean is the plain average."""
    result = rolling_errors([2.0, 4.0, 6.0, 8.0], window=4)
    assert abs(result - 5.0) < 1e-9


def test_more_values_than_window():
    """Only the most recent `window` values contribute to the mean."""
    result = rolling_errors([100.0, 1.0, 2.0, 3.0, 4.0], window=4)
    assert abs(result - 2.5) < 1e-9


def test_zero_error_counts():
    """A window of all zeros should yield a mean of zero."""
    result = rolling_errors([0.0, 0.0, 0.0, 0.0], window=4)
    assert abs(result - 0.0) < 1e-9


def test_single_value_with_window_one():
    """A single observation with window=1 should return that observation."""
    result = rolling_errors([42.0], window=1)
    assert abs(result - 42.0) < 1e-9


def test_raises_on_empty_values():
    """An empty error sequence must raise ValueError."""
    with pytest.raises(ValueError, match="no values"):
        rolling_errors([])


def test_raises_on_non_positive_window():
    """A zero or negative window size must raise ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        rolling_errors([1.0], window=0)


def test_fewer_values_than_window():
    """When fewer values exist than the window, the mean should reflect the actual count."""
    result = rolling_errors([3.0, 6.0], window=4)
    assert abs(result - 4.5) < 1e-9


def test_single_value_with_large_window():
    """A single value with a large window should return that value as the mean."""
    result = rolling_errors([10.0], window=10)
    assert abs(result - 10.0) < 1e-9


def test_two_values_window_eight():
    """Two values with window=8 should average only those two values."""
    result = rolling_errors([5.0, 15.0], window=8)
    assert abs(result - 10.0) < 1e-9


def test_warmup_not_met_returns_none():
    """If warmup_min exceeds available samples, the function should return None."""
    result = rolling_errors([7.0], window=4, warmup_min=3)
    assert result is None
