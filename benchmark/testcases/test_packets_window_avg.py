import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.packets_window_avg import packets_window_avg
else:
    from programs.packets_window_avg import packets_window_avg


def test_full_window_uniform_values():
    """When all samples equal the same value, the mean equals that value."""
    result = packets_window_avg([10.0, 10.0, 10.0, 10.0], window=4)
    assert abs(result - 10.0) < 1e-9


def test_full_window_varied_values():
    """The mean of [2, 4, 6, 8] over window=4 should be 5.0."""
    result = packets_window_avg([2.0, 4.0, 6.0, 8.0], window=4)
    assert abs(result - 5.0) < 1e-9


def test_window_larger_than_data_returns_correct_mean():
    """When fewer samples exist than the window, the mean uses available samples."""
    result = packets_window_avg([3.0, 9.0], window=4)
    assert abs(result - 6.0) < 1e-9


def test_single_sample_window_one():
    """A single-sample input with window=1 returns that sample."""
    result = packets_window_avg([42.0], window=1)
    assert abs(result - 42.0) < 1e-9


def test_empty_values_raises():
    """An empty measurement sequence must raise ValueError."""
    with pytest.raises(ValueError, match="no values"):
        packets_window_avg([])


def test_zero_window_raises():
    """A non-positive window size must raise ValueError."""
    with pytest.raises(ValueError):
        packets_window_avg([1.0], window=0)


def test_partial_window_two_of_four():
    """With only 2 samples and window=4, the mean reflects those 2 samples."""
    result = packets_window_avg([10.0, 20.0], window=4)
    assert abs(result - 15.0) < 1e-9


def test_partial_window_three_of_eight():
    """With 3 samples and window=8, the average of available samples is returned."""
    result = packets_window_avg([6.0, 12.0, 18.0], window=8)
    assert abs(result - 12.0) < 1e-9


def test_warmup_not_met_returns_none():
    """If the available samples are fewer than warmup_min, None is returned."""
    result = packets_window_avg([5.0], window=4, warmup_min=3)
    assert result is None


def test_longer_history_uses_last_window():
    """Only the last window samples are used even when history is longer."""
    result = packets_window_avg([100.0, 200.0, 1.0, 2.0, 3.0, 4.0], window=4)
    assert abs(result - 2.5) < 1e-9
