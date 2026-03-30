import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.views_moving_mean import views_moving_mean
else:
    from programs.views_moving_mean import views_moving_mean


def test_full_window_uniform_values():
    """When all values in the window are identical the mean equals that value."""
    result = views_moving_mean([10, 10, 10, 10], window=4)
    assert abs(result - 10.0) < 1e-9


def test_empty_values_raises():
    """An empty sequence must be rejected immediately."""
    with pytest.raises(ValueError, match="no values"):
        views_moving_mean([])


def test_zero_window_raises():
    """A non-positive window size is invalid."""
    with pytest.raises(ValueError):
        views_moving_mean([1, 2, 3], window=0)


def test_single_value_window_one():
    """A single observation with window=1 should return that observation."""
    result = views_moving_mean([42], window=1)
    assert abs(result - 42.0) < 1e-9


def test_fewer_samples_than_window_mean():
    """When fewer samples exist than the window size, the mean is over available samples."""
    result = views_moving_mean([6, 12], window=4)
    assert abs(result - 9.0) < 1e-9


def test_two_samples_window_four():
    """Two samples with window=4 should average over the two available values."""
    result = views_moving_mean([100, 200], window=4)
    assert abs(result - 150.0) < 1e-9


def test_three_samples_window_ten():
    """Three samples with a large window should yield the average of all three."""
    result = views_moving_mean([10, 20, 30], window=10)
    assert abs(result - 20.0) < 1e-9


def test_one_sample_window_five():
    """A single sample with a larger window should return just that sample."""
    result = views_moving_mean([50], window=5)
    assert abs(result - 50.0) < 1e-9


def test_warmup_suppresses_output():
    """If not enough samples exist to meet warmup_min the result is None."""
    result = views_moving_mean([10], window=4, warmup_min=3)
    assert result is None


def test_exact_window_different_values():
    """The rolling mean over exactly window-many distinct values is their arithmetic mean."""
    result = views_moving_mean([2, 4, 6, 8], window=4)
    assert abs(result - 5.0) < 1e-9
