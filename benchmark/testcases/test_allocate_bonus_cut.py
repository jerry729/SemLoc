import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.allocate_bonus_cut import allocate_bonus_cut
else:
    from programs.allocate_bonus_cut import allocate_bonus_cut


def test_equal_split_no_fee():
    """Equal ratios with no fee should distribute the pool equally."""
    result = allocate_bonus_cut(100.0, [1, 1, 1])
    for payout in result:
        assert abs(payout - 100.0 / 3) < 1e-9


def test_weighted_split_no_fee():
    """Weighted ratios without a fee should distribute proportionally."""
    result = allocate_bonus_cut(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant should receive the entire pool when there is no fee."""
    result = allocate_bonus_cut(500.0, [5])
    assert abs(result[0] - 500.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero pool should yield zero payouts regardless of ratios."""
    result = allocate_bonus_cut(0.0, [1, 2, 3])
    assert all(abs(s) < 1e-9 for s in result)


def test_empty_ratios_raises():
    """An empty ratios list must raise ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        allocate_bonus_cut(100.0, [])


def test_fee_deducted_from_total_pool():
    """The fee should be deducted once from the total pool, not per participant."""
    result = allocate_bonus_cut(100.0, [1, 1], fee=20.0)
    total_distributed = sum(result)
    assert abs(total_distributed - 80.0) < 1e-9


def test_fee_equal_to_amount_yields_zero_payouts():
    """When the fee equals the pool, every participant should receive zero."""
    result = allocate_bonus_cut(50.0, [3, 7], fee=50.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_fee_larger_than_amount_clamps_to_zero():
    """A fee exceeding the pool should result in zero payouts (no negatives)."""
    result = allocate_bonus_cut(30.0, [1, 1, 1], fee=100.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_total_payout_equals_pool_minus_fee():
    """Sum of payouts must equal the pool minus the one-time fee."""
    result = allocate_bonus_cut(1000.0, [2, 3, 5], fee=100.0)
    assert abs(sum(result) - 900.0) < 1e-9


def test_fee_with_unequal_ratios_preserves_proportions():
    """After fee deduction, shares should remain proportional to their ratios."""
    result = allocate_bonus_cut(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9
