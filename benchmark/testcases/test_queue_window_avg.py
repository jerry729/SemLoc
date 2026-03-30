import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.queue_window_avg import queue_window_avg
else:
    from programs.queue_window_avg import queue_window_avg


def test_exact_window_match():
    """When the series length equals the window, the mean is the series average."""
    result = queue_window_avg([2.0, 4.0, 6.0], window=3)
    assert abs(result - 4.0) < 1e-9


def test_window_larger_than_series():
    """When fewer samples exist than the window size, the average covers all samples."""
    result = queue_window_avg([10.0, 20.0], window=5)
    assert abs(result - 15.0) < 1e-9


def test_single_value_window_one():
    """A single-element series with window=1 returns that element."""
    result = queue_window_avg([42.0], window=1)
    assert abs(result - 42.0) < 1e-9


def test_warmup_not_met_returns_none():
    """If the tail has fewer samples than warmup_min, None is returned."""
    result = queue_window_avg([5.0], window=3, warmup_min=3)
    assert result is None


def test_empty_series_raises():
    """An empty series must raise ValueError."""
    with pytest.raises(ValueError, match="empty series"):
        queue_window_avg([])


def test_zero_window_raises():
    """A non-positive window must raise ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        queue_window_avg([1.0], window=0)


def test_two_samples_with_window_five():
    """Two samples with a window of five should yield the average of those two values."""
    result = queue_window_avg([3.0, 9.0], window=5)
    assert abs(result - 6.0) < 1e-9


def test_single_value_with_large_window():
    """A single sample with a large window should return that sample as the mean."""
    result = queue_window_avg([7.0], window=10)
    assert abs(result - 7.0) < 1e-9


def test_trailing_window_selects_last_elements():
    """Only the last 'window' elements should be considered for the average."""
    result = queue_window_avg([100.0, 200.0, 1.0, 2.0, 3.0], window=3)
    assert abs(result - 2.0) < 1e-9


def test_four_samples_window_ten():
    """Four samples with window=10 should average all four values."""
    result = queue_window_avg([2.0, 4.0, 6.0, 8.0], window=10)
    assert abs(result - 5.0) < 1e-9
