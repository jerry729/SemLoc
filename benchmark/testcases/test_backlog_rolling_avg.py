import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.backlog_rolling_avg import backlog_rolling_avg
else:
    from programs.backlog_rolling_avg import backlog_rolling_avg


def test_exact_window_match():
    """When the number of values equals the window, the mean is the arithmetic average of all values."""
    result = backlog_rolling_avg([10, 20, 30, 40], window=4)
    assert abs(result - 25.0) < 1e-9


def test_more_values_than_window():
    """Only the last *window* values should contribute to the average."""
    result = backlog_rolling_avg([100, 200, 10, 20, 30, 40], window=4)
    assert abs(result - 25.0) < 1e-9


def test_single_value_window_one():
    """A single-element list with window=1 should return that element."""
    result = backlog_rolling_avg([42.0], window=1)
    assert abs(result - 42.0) < 1e-9


def test_raises_on_zero_window():
    """A non-positive window size should be rejected immediately."""
    with pytest.raises(ValueError, match="window must be positive"):
        backlog_rolling_avg([1, 2, 3], window=0)


def test_raises_on_empty_values():
    """An empty sequence must trigger a ValueError."""
    with pytest.raises(ValueError, match="no values"):
        backlog_rolling_avg([], window=4)


def test_fewer_values_than_window_average():
    """When fewer samples exist than the window, the average should reflect only available data."""
    result = backlog_rolling_avg([10, 30], window=4)
    assert abs(result - 20.0) < 1e-9


def test_two_values_window_five():
    """With 2 values and window=5, the rolling average should be the mean of those 2 values."""
    result = backlog_rolling_avg([6, 14], window=5)
    assert abs(result - 10.0) < 1e-9


def test_single_value_large_window():
    """A single sample with a large window should return that sample as the average."""
    result = backlog_rolling_avg([50.0], window=10)
    assert abs(result - 50.0) < 1e-9


def test_warmup_not_met_returns_none():
    """If the number of recent samples is below the warmup threshold, None is returned."""
    result = backlog_rolling_avg([5.0], window=4, warmup_min=3)
    assert result is None


def test_three_values_window_eight():
    """Three values with a window of eight should yield the mean of the three available values."""
    result = backlog_rolling_avg([12, 24, 36], window=8)
    assert abs(result - 24.0) < 1e-9
