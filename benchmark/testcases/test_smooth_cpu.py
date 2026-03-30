import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.smooth_cpu import smooth_cpu
else:
    from programs.smooth_cpu import smooth_cpu


def test_exact_window_match():
    """When the number of samples equals the window, the mean is the simple average."""
    result = smooth_cpu([10.0, 20.0, 30.0], window=3)
    assert abs(result - 20.0) < 1e-9


def test_window_larger_than_series():
    """When fewer samples than the window exist, the mean should equal the average of all available samples."""
    result = smooth_cpu([40.0, 60.0], window=5)
    assert abs(result - 50.0) < 1e-9


def test_single_sample_single_window():
    """A single sample with window=1 should return that sample's value."""
    result = smooth_cpu([75.0], window=1)
    assert abs(result - 75.0) < 1e-9


def test_values_exceed_upper_bound_are_clamped():
    """Samples above 100% should be clamped to 100 before averaging."""
    result = smooth_cpu([200.0, 200.0, 200.0], window=3)
    assert abs(result - 100.0) < 1e-9


def test_negative_values_are_clamped_to_zero():
    """Negative CPU readings should be clamped to 0."""
    result = smooth_cpu([-50.0, -10.0], window=2)
    assert abs(result - 0.0) < 1e-9


def test_empty_series_raises():
    """An empty series must raise ValueError."""
    with pytest.raises(ValueError, match="empty series"):
        smooth_cpu([])


def test_zero_window_raises():
    """A non-positive window must raise ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        smooth_cpu([1.0], window=0)


def test_two_samples_with_window_five():
    """With 2 samples and window=5, the rolling mean should average the 2 available values."""
    result = smooth_cpu([10.0, 30.0], window=5)
    assert abs(result - 20.0) < 1e-9


def test_one_sample_with_default_window():
    """One sample with the default window of 3 should return that sample's value as the mean."""
    result = smooth_cpu([42.0])
    assert abs(result - 42.0) < 1e-9


def test_long_series_only_tail_matters():
    """Only the trailing window samples should contribute to the mean."""
    values = [0.0, 0.0, 0.0, 0.0, 30.0, 60.0, 90.0]
    result = smooth_cpu(values, window=3)
    assert abs(result - 60.0) < 1e-9
