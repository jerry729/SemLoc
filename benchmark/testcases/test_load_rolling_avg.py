import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.load_rolling_avg import load_rolling_avg
else:
    from programs.load_rolling_avg import load_rolling_avg


def test_full_window_uniform_load():
    """A uniform series spanning the full window should yield that constant value."""
    result = load_rolling_avg([50.0, 50.0, 50.0, 50.0, 50.0], window=5)
    assert abs(result - 50.0) < 1e-9


def test_series_longer_than_window():
    """Only the last `window` samples should contribute to the average."""
    result = load_rolling_avg([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0], window=3)
    assert abs(result - 60.0) < 1e-9


def test_empty_series_raises():
    """An empty series is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="no samples"):
        load_rolling_avg([])


def test_invalid_window_raises():
    """A non-positive window must raise ValueError."""
    with pytest.raises(ValueError, match="invalid window"):
        load_rolling_avg([1.0, 2.0], window=0)


def test_warmup_returns_none_for_single_sample():
    """With default warmup_min=2, a single sample should return None."""
    result = load_rolling_avg([42.0], window=5, warmup_min=2)
    assert result is None


def test_two_samples_with_window_five():
    """Two samples with window=5 should compute the average of those two samples."""
    result = load_rolling_avg([10.0, 30.0], window=5, warmup_min=2)
    assert abs(result - 20.0) < 1e-9


def test_three_samples_with_window_five():
    """Three samples with a larger window should average over the available data."""
    result = load_rolling_avg([10.0, 20.0, 30.0], window=5, warmup_min=2)
    assert abs(result - 20.0) < 1e-9


def test_four_samples_with_window_ten():
    """When series has fewer elements than the window, the average should use actual count."""
    result = load_rolling_avg([100.0, 200.0, 300.0, 400.0], window=10, warmup_min=2)
    assert abs(result - 250.0) < 1e-9


def test_single_sample_with_warmup_one():
    """With warmup_min=1, a single sample should return the sample value itself."""
    result = load_rolling_avg([77.0], window=5, warmup_min=1)
    assert abs(result - 77.0) < 1e-9


def test_window_exceeds_max_raises():
    """A window larger than the configured maximum must raise ValueError."""
    with pytest.raises(ValueError):
        load_rolling_avg([1.0], window=1001)
