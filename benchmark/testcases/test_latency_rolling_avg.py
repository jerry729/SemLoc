import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.latency_rolling_avg import latency_rolling_avg
else:
    from programs.latency_rolling_avg import latency_rolling_avg


def test_full_window_average():
    """When the series length matches the window, the average equals the arithmetic mean of all samples."""
    result = latency_rolling_avg([10.0, 20.0, 30.0, 40.0, 50.0], window=5)
    assert abs(result - 30.0) < 1e-9


def test_series_longer_than_window():
    """Only the last `window` samples should contribute to the rolling average."""
    result = latency_rolling_avg([1.0, 2.0, 3.0, 100.0, 200.0, 300.0], window=3)
    assert abs(result - 200.0) < 1e-9


def test_empty_series_raises():
    """An empty latency series must raise ValueError since no data is available."""
    with pytest.raises(ValueError, match="no samples"):
        latency_rolling_avg([])


def test_invalid_window_raises():
    """A non-positive window is invalid and must be rejected."""
    with pytest.raises(ValueError, match="invalid window"):
        latency_rolling_avg([1.0], window=0)


def test_warmup_not_met_returns_none():
    """When the tail has fewer samples than warmup_min, the result should be None."""
    result = latency_rolling_avg([42.0], window=5, warmup_min=3)
    assert result is None


def test_single_sample_with_large_window():
    """A single sample with a window larger than the series should return the sample value as the average."""
    result = latency_rolling_avg([75.0], window=10, warmup_min=1)
    assert abs(result - 75.0) < 1e-9


def test_two_samples_window_larger_than_series():
    """When the series has 2 samples and window is 5, the average should equal the mean of those 2 samples."""
    result = latency_rolling_avg([100.0, 200.0], window=5, warmup_min=2)
    assert abs(result - 150.0) < 1e-9


def test_three_samples_window_ten():
    """Three samples averaged over a window of 10 should yield the true mean of the three samples."""
    result = latency_rolling_avg([30.0, 60.0, 90.0], window=10, warmup_min=2)
    assert abs(result - 60.0) < 1e-9


def test_window_one_returns_last_sample():
    """A window of 1 should always return the most recent latency measurement."""
    result = latency_rolling_avg([5.0, 10.0, 15.0, 20.0], window=1, warmup_min=1)
    assert abs(result - 20.0) < 1e-9


def test_uniform_series_average_equals_value():
    """For a uniform series the rolling average should equal the constant value regardless of window."""
    result = latency_rolling_avg([50.0, 50.0, 50.0], window=3)
    assert abs(result - 50.0) < 1e-9
