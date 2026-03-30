import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.water_allocator import water_allocator
else:
    from programs.water_allocator import water_allocator


def test_integer_total_exact_division_pass():
    """When total divides evenly, allocations sum to total."""
    result = water_allocator(100, [1, 1, 1, 1])
    assert sum(result) == 100


def test_truncation_sum_equals_total_fail():
    """Sum of integer allocations must equal total (largest remainder corrects floor).
    Fails when remainder is simply discarded."""
    result = water_allocator(10, [1, 1, 1])
    assert sum(result) == 10, f"sum={sum(result)}, expected 10 (lost remainder)"


def test_unequal_weights_sum_preserved_fail():
    """Unequal weights; sum must still equal total."""
    result = water_allocator(7, [3, 3, 1])
    assert sum(result) == 7, f"sum={sum(result)}, expected 7"


def test_single_recipient_pass():
    """Single recipient gets everything."""
    result = water_allocator(15, [1])
    assert result == [15]


def test_all_integer_allocations_pass():
    """Results must be non-negative integers."""
    result = water_allocator(12, [2, 3, 1])
    assert all(isinstance(v, int) and v >= 0 for v in result)
