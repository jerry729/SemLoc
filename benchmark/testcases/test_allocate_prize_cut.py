import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.allocate_prize_cut import allocate_prize_cut
else:
    from programs.allocate_prize_cut import allocate_prize_cut


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield equal shares summing to the pool."""
    result = allocate_prize_cut(100.0, [1, 1, 1, 1])
    assert all(abs(s - 25.0) < 1e-9 for s in result)


def test_weighted_split_no_fee():
    """Unequal ratios distribute the full pool proportionally when fee is zero."""
    result = allocate_prize_cut(200.0, [3, 1])
    assert abs(result[0] - 150.0) < 1e-9
    assert abs(result[1] - 50.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant receives the entire pool when there is no fee."""
    result = allocate_prize_cut(500.0, [7])
    assert abs(result[0] - 500.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratios list must raise ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        allocate_prize_cut(100.0, [])


def test_negative_amount_raises():
    """A negative prize pool must be rejected."""
    with pytest.raises(ValueError, match="negative amount"):
        allocate_prize_cut(-50.0, [1, 1])


def test_fee_deducted_from_total_pool():
    """The fee should be subtracted from the total pool before splitting."""
    result = allocate_prize_cut(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_larger_than_amount_yields_zero():
    """When the fee exceeds the pool, all payouts should be zero."""
    result = allocate_prize_cut(50.0, [1, 1, 1], fee=100.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_total_payout_equals_pool_minus_fee():
    """The sum of all shares must equal the pool after fee deduction."""
    result = allocate_prize_cut(1000.0, [5, 3, 2], fee=100.0)
    assert abs(sum(result) - 900.0) < 1e-9


def test_fee_with_unequal_ratios():
    """Fee should reduce the total pool; ratios still govern proportionality."""
    result = allocate_prize_cut(200.0, [3, 1], fee=40.0)
    assert abs(result[0] - 120.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_zero_amount_with_fee():
    """A zero pool with any fee should yield all-zero payouts."""
    result = allocate_prize_cut(0.0, [1, 2, 3], fee=10.0)
    assert all(abs(s) < 1e-9 for s in result)
