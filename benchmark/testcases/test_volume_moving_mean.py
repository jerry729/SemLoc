import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.volume_moving_mean import volume_moving_mean
else:
    from programs.volume_moving_mean import volume_moving_mean


def test_exact_window_match_four_samples():
    """When sample count equals window size, the mean equals the arithmetic average."""
    result = volume_moving_mean([100, 200, 300, 400], window=4)
    assert abs(result - 250.0) < 1e-9


def test_more_samples_than_window():
    """Only the trailing window samples should contribute to the mean."""
    result = volume_moving_mean([10, 20, 30, 40, 50], window=3)
    assert abs(result - 40.0) < 1e-9


def test_single_sample_window_one():
    """A single-element sequence with window=1 should return that element."""
    result = volume_moving_mean([42.0], window=1)
    assert abs(result - 42.0) < 1e-9


def test_invalid_window_raises():
    """A non-positive window must raise ValueError."""
    with pytest.raises(ValueError):
        volume_moving_mean([1, 2, 3], window=0)


def test_empty_values_raises():
    """An empty sequence must raise ValueError."""
    with pytest.raises(ValueError):
        volume_moving_mean([], window=4)


def test_fewer_samples_than_window_mean_accuracy():
    """When fewer samples exist than the window, the mean should be their true average."""
    result = volume_moving_mean([100, 200], window=5)
    assert abs(result - 150.0) < 1e-9


def test_single_sample_large_window():
    """One sample with a large window should return that sample as the mean."""
    result = volume_moving_mean([500], window=10)
    assert abs(result - 500.0) < 1e-9


def test_two_samples_window_four():
    """Two samples with a window of four: mean should be the average of the two samples."""
    result = volume_moving_mean([80, 120], window=4)
    assert abs(result - 100.0) < 1e-9


def test_three_samples_window_eight():
    """Three samples with window of eight should produce the average of all three."""
    result = volume_moving_mean([10, 20, 30], window=8)
    assert abs(result - 20.0) < 1e-9


def test_warmup_not_met_returns_none():
    """If the number of available samples is below warmup_min, None is returned."""
    result = volume_moving_mean([100], window=4, warmup_min=3)
    assert result is None
