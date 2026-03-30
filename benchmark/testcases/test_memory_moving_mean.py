import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.memory_moving_mean import memory_moving_mean
else:
    from programs.memory_moving_mean import memory_moving_mean


def test_full_window_exact_samples():
    """When the series length equals the window size the average is the arithmetic mean of all samples."""
    series = [100.0, 200.0, 300.0, 400.0, 500.0]
    result = memory_moving_mean(series, window=5)
    assert abs(result - 300.0) < 1e-9


def test_series_longer_than_window():
    """Only the last *window* samples are included when the series exceeds the window."""
    series = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
    result = memory_moving_mean(series, window=5)
    assert abs(result - 50.0) < 1e-9


def test_empty_series_raises():
    """An empty series must raise a ValueError because no average can be computed."""
    with pytest.raises(ValueError, match="no samples"):
        memory_moving_mean([])


def test_zero_window_raises():
    """A non-positive window is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="invalid window"):
        memory_moving_mean([1.0, 2.0], window=0)


def test_warmup_not_met_returns_none():
    """When the number of available tail samples is below warmup_min, None is returned."""
    result = memory_moving_mean([42.0], window=5, warmup_min=3)
    assert result is None


def test_fewer_samples_than_window_average():
    """When the series has fewer elements than the window the average should reflect only the available samples."""
    series = [200.0, 400.0]
    result = memory_moving_mean(series, window=5, warmup_min=2)
    assert abs(result - 300.0) < 1e-9


def test_single_sample_with_window_one():
    """A single-sample series with window=1 should return that sample's value."""
    result = memory_moving_mean([128.5], window=1, warmup_min=1)
    assert abs(result - 128.5) < 1e-9


def test_three_samples_window_ten():
    """Three samples with a large window should average across only the three available samples."""
    series = [10.0, 20.0, 30.0]
    result = memory_moving_mean(series, window=10, warmup_min=2)
    assert abs(result - 20.0) < 1e-9


def test_two_samples_window_four():
    """Two samples with window=4 should yield the mean of those two samples."""
    series = [50.0, 150.0]
    result = memory_moving_mean(series, window=4, warmup_min=2)
    assert abs(result - 100.0) < 1e-9


def test_window_exceeds_max_raises():
    """A window larger than the maximum allowed limit must raise ValueError."""
    with pytest.raises(ValueError, match="exceeds maximum"):
        memory_moving_mean([1.0], window=10_001)
