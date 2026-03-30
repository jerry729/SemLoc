import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.smooth_throughput import smooth_throughput
else:
    from programs.smooth_throughput import smooth_throughput


def test_full_window_uniform_values():
    """When all samples in a full window are equal, the average equals that value."""
    result = smooth_throughput([100.0] * 10, window=5)
    assert abs(result - 100.0) < 1e-9


def test_empty_series_raises():
    """An empty series must raise ValueError because no throughput data exists."""
    with pytest.raises(ValueError, match="no samples"):
        smooth_throughput([])


def test_zero_window_raises():
    """A non-positive window size is invalid and must be rejected."""
    with pytest.raises(ValueError, match="invalid window"):
        smooth_throughput([1.0, 2.0], window=0)


def test_warmup_returns_none():
    """When available samples are fewer than warmup_min, None must be returned."""
    result = smooth_throughput([42.0], window=5, warmup_min=3)
    assert result is None


def test_exactly_warmup_threshold():
    """At exactly the warmup threshold, a numeric result should be returned."""
    result = smooth_throughput([10.0, 20.0], window=5, warmup_min=2)
    assert result is not None


def test_series_shorter_than_window_average():
    """When the series has fewer elements than the window, the average should
    reflect only the available samples (arithmetic mean of the tail)."""
    result = smooth_throughput([3.0, 6.0, 9.0], window=10, warmup_min=2)
    assert abs(result - 6.0) < 1e-9


def test_two_element_series_with_window_five():
    """A two-element series with default window should average those two elements."""
    result = smooth_throughput([4.0, 8.0], window=5, warmup_min=2)
    assert abs(result - 6.0) < 1e-9


def test_large_window_single_sample_with_warmup_one():
    """With warmup_min=1 and a single sample, the average equals that sample."""
    result = smooth_throughput([50.0], window=100, warmup_min=1)
    assert abs(result - 50.0) < 1e-9


def test_tail_three_of_five():
    """When three elements exist and window is five, the moving average is
    the arithmetic mean of those three elements."""
    result = smooth_throughput([10.0, 20.0, 30.0], window=5, warmup_min=2)
    assert abs(result - 20.0) < 1e-9


def test_window_equals_series_length():
    """When the window exactly matches the series length, the result is the
    overall arithmetic mean of the series."""
    result = smooth_throughput([2.0, 4.0, 6.0, 8.0, 10.0], window=5)
    assert abs(result - 6.0) < 1e-9
