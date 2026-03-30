import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.smooth_pressure import smooth_pressure
else:
    from programs.smooth_pressure import smooth_pressure


def test_full_window_uniform_readings():
    """A full window of identical pressure readings should return that reading."""
    result = smooth_pressure([100.0, 100.0, 100.0, 100.0], window=4)
    assert abs(result - 100.0) < 1e-9


def test_non_positive_window_raises():
    """A non-positive window size is physically meaningless and must be rejected."""
    with pytest.raises(ValueError, match="window must be positive"):
        smooth_pressure([500.0], window=0)


def test_empty_values_raises():
    """Processing requires at least one reading; an empty sequence is invalid."""
    with pytest.raises(ValueError, match="no values"):
        smooth_pressure([], window=3)


def test_out_of_range_pressure_raises():
    """Readings beyond the physical pressure bounds must be rejected."""
    with pytest.raises(ValueError):
        smooth_pressure([-1.0, 100.0], window=2)


def test_full_window_known_average():
    """Mean of [10, 20, 30, 40] with window=4 should be 25.0."""
    result = smooth_pressure([10.0, 20.0, 30.0, 40.0], window=4)
    assert abs(result - 25.0) < 1e-9


def test_fewer_samples_than_window_computes_correct_mean():
    """When fewer samples exist than the window, the mean should use the actual count."""
    result = smooth_pressure([200.0, 400.0], window=5)
    assert abs(result - 300.0) < 1e-9


def test_single_sample_with_large_window():
    """A single sample with a window larger than the data should return that sample."""
    result = smooth_pressure([750.0], window=10)
    assert abs(result - 750.0) < 1e-9


def test_window_of_one_returns_last_reading():
    """Window of 1 must always return the most recent reading."""
    result = smooth_pressure([100.0, 200.0, 300.0], window=1)
    assert abs(result - 300.0) < 1e-9


def test_warmup_threshold_returns_none():
    """If available samples are below the warmup minimum, result must be None."""
    result = smooth_pressure([500.0], window=4, warmup_min=3)
    assert result is None


def test_two_samples_window_four_mean():
    """Two samples with window=4: mean should equal the two-sample average."""
    result = smooth_pressure([1000.0, 3000.0], window=4)
    assert abs(result - 2000.0) < 1e-9
