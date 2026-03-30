import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.sensor_window_avg import sensor_window_avg
else:
    from programs.sensor_window_avg import sensor_window_avg


def test_exact_window_match():
    """When the number of samples equals the window size, the mean equals the simple average."""
    result = sensor_window_avg([2.0, 4.0, 6.0], window=3)
    assert abs(result - 4.0) < 1e-9


def test_more_samples_than_window():
    """Only the last *window* samples should influence the result."""
    result = sensor_window_avg([100.0, 200.0, 1.0, 2.0, 3.0], window=3)
    assert abs(result - 2.0) < 1e-9


def test_zero_value_samples():
    """Sensor readings of exactly zero should be averaged correctly."""
    result = sensor_window_avg([0.0, 0.0, 0.0], window=3)
    assert abs(result - 0.0) < 1e-9


def test_single_sample_default_window():
    """A single reading with the default window should return that reading's value."""
    result = sensor_window_avg([42.0])
    assert abs(result - 42.0) < 1e-9


def test_empty_samples_raises():
    """An empty sample list is invalid; the pipeline must reject it."""
    with pytest.raises(ValueError, match="no samples"):
        sensor_window_avg([])


def test_non_positive_window_raises():
    """A non-positive window size is physically meaningless and must be rejected."""
    with pytest.raises(ValueError, match="window must be positive"):
        sensor_window_avg([1.0], window=0)


def test_fewer_samples_than_window():
    """When fewer readings exist than the window, the average should reflect only available samples."""
    result = sensor_window_avg([10.0, 20.0], window=5)
    assert abs(result - 15.0) < 1e-9


def test_single_sample_large_window():
    """One sample with a large window should still return that sample's value."""
    result = sensor_window_avg([7.5], window=10)
    assert abs(result - 7.5) < 1e-9


def test_min_samples_not_met_returns_none():
    """When available readings are below the warmup threshold, None signals insufficient data."""
    result = sensor_window_avg([5.0], window=5, min_samples=3)
    assert result is None


def test_window_exceeds_max_raises():
    """Extremely large window sizes should be rejected to prevent resource exhaustion."""
    with pytest.raises(ValueError, match="exceeds maximum"):
        sensor_window_avg([1.0], window=2000)
