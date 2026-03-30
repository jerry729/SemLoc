import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.invoice_merge_stream import invoice_merge_stream
else:
    from programs.invoice_merge_stream import invoice_merge_stream


def test_disjoint_streams_interleave_correctly():
    """Two non-overlapping ledger streams should produce a fully sorted union."""
    result = invoice_merge_stream([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_empty_left_stream_returns_right():
    """Merging an empty primary ledger with a populated secondary yields the secondary."""
    result = invoice_merge_stream([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_empty_right_stream_returns_left():
    """Merging a populated primary ledger with an empty secondary yields the primary."""
    result = invoice_merge_stream([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_both_streams_empty():
    """Merging two empty ledgers should produce an empty result."""
    result = invoice_merge_stream([], [])
    assert result == []


def test_unsorted_input_raises_value_error():
    """An unsorted input stream must be rejected before merging."""
    with pytest.raises(ValueError):
        invoice_merge_stream([5, 3, 1], [2, 4, 6])


def test_duplicate_ids_across_streams_preserved():
    """Invoice IDs appearing in both streams should each contribute a copy."""
    result = invoice_merge_stream([1, 2, 3], [2, 3, 4])
    assert result == [1, 2, 2, 3, 3, 4]


def test_single_shared_element_at_end():
    """When both streams share only the last element, both copies must be present."""
    result = invoice_merge_stream([1, 5], [3, 5])
    assert result == [1, 3, 5, 5]


def test_identical_streams_preserve_all_entries():
    """Two identical streams should produce exactly twice as many entries."""
    left = [10, 20, 30]
    right = [10, 20, 30]
    result = invoice_merge_stream(left, right)
    assert result == [10, 10, 20, 20, 30, 30]


def test_single_common_element_only():
    """When both streams contain exactly one identical invoice ID, both copies appear."""
    result = invoice_merge_stream([42], [42])
    assert result == [42, 42]


def test_large_overlap_at_tail_preserves_count():
    """Multiple overlapping tail elements should all be retained in merged output."""
    left = [1, 2, 3, 4, 5]
    right = [3, 4, 5]
    result = invoice_merge_stream(left, right)
    assert result == [1, 2, 3, 3, 4, 4, 5, 5]
