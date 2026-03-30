import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.energy_window_avg import energy_window_avg
else:
    from programs.energy_window_avg import energy_window_avg


def test_exact_window_match():
    """When the number of values equals the window size, the mean equals the simple average."""
    result = energy_window_avg([10.0, 20.0, 30.0, 40.0], window=4)
    assert abs(result - 25.0) < 1e-9


def test_window_larger_than_data_returns_correct_average():
    """If fewer readings exist than the window size, the average should use only available readings."""
    result = energy_window_avg([6.0, 12.0], window=4)
    assert abs(result - 9.0) < 1e-9


def test_single_value_with_default_window():
    """A single reading should return exactly that reading as the average."""
    result = energy_window_avg([42.0])
    assert abs(result - 42.0) < 1e-9


def test_two_values_window_larger():
    """Two readings with a window of 5 should produce the mean of those two readings."""
    result = energy_window_avg([100.0, 200.0], window=5)
    assert abs(result - 150.0) < 1e-9


def test_three_values_window_of_ten():
    """Three readings with a window of 10 should average all three readings."""
    result = energy_window_avg([30.0, 60.0, 90.0], window=10)
    assert abs(result - 60.0) < 1e-9


def test_warmup_not_met_returns_none():
    """When fewer readings are available than warmup_min, None must be returned."""
    result = energy_window_avg([5.0], window=4, warmup_min=3)
    assert result is None


def test_zero_window_raises():
    """A non-positive window size is invalid and should raise ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        energy_window_avg([1.0, 2.0], window=0)


def test_empty_values_raises():
    """An empty readings list should raise ValueError."""
    with pytest.raises(ValueError, match="no values"):
        energy_window_avg([])


def test_window_equals_data_length_uniform_values():
    """Uniform readings must yield that uniform value regardless of window size."""
    result = energy_window_avg([7.0, 7.0, 7.0], window=3)
    assert abs(result - 7.0) < 1e-9


def test_trailing_window_selects_most_recent():
    """Only the trailing window elements should contribute to the average."""
    result = energy_window_avg([1.0, 2.0, 3.0, 10.0, 20.0], window=2)
    assert abs(result - 15.0) < 1e-9
