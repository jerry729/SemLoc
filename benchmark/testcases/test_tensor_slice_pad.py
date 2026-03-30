import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.tensor_slice_pad import tensor_slice_pad
else:
    from programs.tensor_slice_pad import tensor_slice_pad


def test_slice_fully_within_bounds():
    """A slice entirely within the data should return the exact sub-list."""
    data = [10, 20, 30, 40, 50]
    result = tensor_slice_pad(data, 1, 4)
    assert result == [20, 30, 40]


def test_slice_entire_list():
    """Slicing the full range of the data should reproduce it exactly."""
    data = [1, 2, 3, 4, 5]
    result = tensor_slice_pad(data, 0, 5)
    assert result == [1, 2, 3, 4, 5]


def test_slice_with_partial_padding():
    """When the slice extends past the end, trailing pad values should fill the gap."""
    data = [7, 8, 9]
    result = tensor_slice_pad(data, 1, 5)
    assert result == [8, 9, 0, 0]


def test_slice_completely_beyond_data():
    """A window entirely past the data should be filled with pad values only."""
    data = [1, 2]
    result = tensor_slice_pad(data, 5, 8, pad=-1)
    assert result == [-1, -1, -1]


def test_result_length_matches_requested_window():
    """The returned list length must always equal end - start."""
    data = [100, 200, 300]
    result = tensor_slice_pad(data, 0, 6)
    assert len(result) == 6


def test_no_padding_needed_length_preserved():
    """When no padding is needed the output length must match the window size."""
    data = [5, 10, 15, 20]
    result = tensor_slice_pad(data, 0, 4)
    assert len(result) == 4


def test_empty_window_returns_empty_list():
    """Requesting a zero-width window (start == end) should yield an empty list."""
    data = [1, 2, 3]
    result = tensor_slice_pad(data, 2, 2)
    assert result == []


def test_negative_start_raises_value_error():
    """A negative start index is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        tensor_slice_pad([1, 2, 3], -1, 2)


def test_end_less_than_start_raises_value_error():
    """An inverted range must raise ValueError."""
    with pytest.raises(ValueError):
        tensor_slice_pad([1, 2, 3], 3, 1)


def test_custom_pad_value_propagated():
    """A user-supplied pad value should appear in every padded position."""
    data = [42]
    result = tensor_slice_pad(data, 0, 4, pad=999)
    assert result == [42, 999, 999, 999]
