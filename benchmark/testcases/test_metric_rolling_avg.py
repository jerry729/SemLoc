import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.metric_rolling_avg import metric_rolling_avg
else:
    from programs.metric_rolling_avg import metric_rolling_avg


def test_exact_window_match():
    """When the number of values equals the window, the average is the arithmetic mean of all values."""
    result = metric_rolling_avg([10.0, 20.0, 30.0, 40.0, 50.0], window=5)
    assert abs(result - 30.0) < 1e-9


def test_more_values_than_window():
    """Only the trailing window values should contribute to the average."""
    result = metric_rolling_avg([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], window=5)
    assert abs(result - 5.0) < 1e-9


def test_single_value_default_window():
    """A single metric reading should yield that reading as the average."""
    result = metric_rolling_avg([42.0], window=5)
    assert abs(result - 42.0) < 1e-9


def test_two_values_window_larger_than_data():
    """When fewer values exist than the window size, the average should reflect only available values."""
    result = metric_rolling_avg([10.0, 20.0], window=5)
    assert abs(result - 15.0) < 1e-9


def test_three_values_window_of_ten():
    """Three readings with a large window should produce the mean of those three readings."""
    result = metric_rolling_avg([6.0, 12.0, 18.0], window=10)
    assert abs(result - 12.0) < 1e-9


def test_window_of_one_returns_last_value():
    """A window of 1 should always return the most recent metric value."""
    result = metric_rolling_avg([5.0, 10.0, 15.0], window=1)
    assert abs(result - 15.0) < 1e-9


def test_empty_values_raises_error():
    """An empty metric stream must raise ValueError since no average is computable."""
    with pytest.raises(ValueError):
        metric_rolling_avg([])


def test_zero_window_raises_error():
    """A non-positive window is invalid and must be rejected."""
    with pytest.raises(ValueError):
        metric_rolling_avg([1.0, 2.0], window=0)


def test_min_samples_suppresses_output():
    """If the tail contains fewer values than min_samples, the function should return None."""
    result = metric_rolling_avg([100.0], window=5, min_samples=3)
    assert result is None


def test_negative_values_average():
    """Negative metric readings should be averaged correctly."""
    result = metric_rolling_avg([-10.0, -20.0, -30.0], window=3)
    assert abs(result - (-20.0)) < 1e-9
