import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.fuel_moving_mean import fuel_moving_mean
else:
    from programs.fuel_moving_mean import fuel_moving_mean


def test_positive_window_required():
    """A non-positive window size should raise ValueError."""
    with pytest.raises(ValueError):
        fuel_moving_mean([10.0, 20.0], window=0)


def test_empty_readings_rejected():
    """An empty readings list must be rejected with ValueError."""
    with pytest.raises(ValueError):
        fuel_moving_mean([])


def test_exact_window_match():
    """When sample count equals window size, the mean should be the true average."""
    result = fuel_moving_mean([2.0, 4.0, 6.0, 8.0], window=4)
    assert abs(result - 5.0) < 1e-9


def test_window_larger_than_samples():
    """When window exceeds available samples, the mean should reflect all readings."""
    result = fuel_moving_mean([10.0, 20.0], window=4)
    assert abs(result - 15.0) < 1e-9


def test_single_reading_single_window():
    """A single reading with window=1 should return that reading exactly."""
    result = fuel_moving_mean([42.5], window=1)
    assert abs(result - 42.5) < 1e-9


def test_warmup_not_met_returns_none():
    """If fewer readings than warmup_min exist in the window, return None."""
    result = fuel_moving_mean([5.0], window=4, warmup_min=3)
    assert result is None


def test_two_readings_window_of_five():
    """With two readings and a window of five, the average should cover both readings."""
    result = fuel_moving_mean([3.0, 7.0], window=5)
    assert abs(result - 5.0) < 1e-9


def test_three_readings_window_of_ten():
    """Three readings with a large window should average all three readings."""
    result = fuel_moving_mean([12.0, 18.0, 24.0], window=10)
    assert abs(result - 18.0) < 1e-9


def test_sliding_window_uses_last_entries():
    """Only the last *window* readings should contribute to the mean."""
    readings = [100.0, 200.0, 10.0, 20.0]
    result = fuel_moving_mean(readings, window=2)
    assert abs(result - 15.0) < 1e-9


def test_single_reading_large_window():
    """A single reading with a large window should return that reading as the mean."""
    result = fuel_moving_mean([7.0], window=100)
    assert abs(result - 7.0) < 1e-9
