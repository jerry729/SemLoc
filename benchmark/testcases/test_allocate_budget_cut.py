import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.allocate_budget_cut import allocate_budget_cut
else:
    from programs.allocate_budget_cut import allocate_budget_cut


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield equal shares summing to the pool."""
    result = allocate_budget_cut(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for s in result:
        assert abs(s - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant with no fee receives the entire pool."""
    result = allocate_budget_cut(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_weighted_split_no_fee():
    """Weighted ratios without a fee should distribute proportionally."""
    result = allocate_budget_cut(300.0, [1, 2, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 100.0) < 1e-9
    assert abs(result[2] - 150.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        allocate_budget_cut(100.0, [])


def test_negative_amount_raises():
    """A negative budget pool is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="negative amount"):
        allocate_budget_cut(-50.0, [1, 2])


def test_fee_deducted_from_total_pool():
    """The fee should be deducted from the total pool before splitting."""
    result = allocate_budget_cut(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_exceeds_pool_gives_zero():
    """When the fee exceeds the pool, all payouts should be zero (floor)."""
    result = allocate_budget_cut(50.0, [1, 1, 1], fee=100.0)
    for s in result:
        assert abs(s) < 1e-9


def test_weighted_split_with_fee():
    """Weighted distribution with a fee: the net pool is distributed proportionally."""
    result = allocate_budget_cut(200.0, [1, 3], fee=40.0)
    net = 160.0
    assert abs(result[0] - net * 0.25) < 1e-9
    assert abs(result[1] - net * 0.75) < 1e-9


def test_total_payouts_equal_net_pool():
    """Sum of all payouts must equal the pool minus the fee."""
    result = allocate_budget_cut(1000.0, [2, 3, 5], fee=100.0)
    assert abs(sum(result) - 900.0) < 1e-9


def test_fee_applied_once_not_per_participant():
    """The fee is a single deduction, not charged per participant."""
    result_2 = allocate_budget_cut(100.0, [1, 1], fee=10.0)
    result_4 = allocate_budget_cut(100.0, [1, 1, 1, 1], fee=10.0)
    assert abs(sum(result_2) - 90.0) < 1e-9
    assert abs(sum(result_4) - 90.0) < 1e-9
