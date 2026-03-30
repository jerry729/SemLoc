import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.percentile_estimator import percentile_estimator
else:
    from programs.percentile_estimator import percentile_estimator


def test_empty_sequence_raises():
    """An empty observation set must raise ValueError."""
    with pytest.raises(ValueError):
        percentile_estimator([])


def test_invalid_quantile_above_one():
    """Quantile values exceeding 1.0 must be rejected."""
    with pytest.raises(ValueError):
        percentile_estimator([1, 2, 3], q=1.5)


def test_invalid_quantile_negative():
    """Negative quantile values must be rejected."""
    with pytest.raises(ValueError):
        percentile_estimator([1, 2, 3], q=-0.1)


def test_median_of_odd_length():
    """The median of a small odd-length sorted list should return the middle value."""
    result = percentile_estimator([10, 20, 30, 40, 50], q=0.5)
    assert result == 30


def test_low_quantile_returns_near_minimum():
    """A very low quantile should return a value near the start of the sorted data."""
    result = percentile_estimator([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], q=0.0)
    assert result == 1


def test_single_element_at_zero_quantile():
    """A single-element list at q=0 should return the sole element."""
    result = percentile_estimator([42], q=0.0)
    assert result == 42


def test_single_element_at_full_quantile():
    """A single-element list at q=1.0 should return the sole element."""
    result = percentile_estimator([42], q=1.0)
    assert result == 42


def test_100th_percentile_returns_maximum():
    """Requesting q=1.0 on a multi-element list should return the maximum value."""
    data = list(range(1, 101))
    result = percentile_estimator(data, q=1.0)
    assert result == 100


def test_95th_percentile_large_dataset():
    """The 95th percentile of 1..100 should return a value near the top of the range."""
    data = list(range(1, 101))
    result = percentile_estimator(data, q=0.95)
    assert result == 96


def test_default_quantile_on_twenty_elements():
    """The default 0.95 quantile on a 20-element dataset should return the last element."""
    data = list(range(1, 21))
    result = percentile_estimator(data)
    assert result == 20
