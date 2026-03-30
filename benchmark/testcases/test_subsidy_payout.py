import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.subsidy_payout import subsidy_payout
else:
    from programs.subsidy_payout import subsidy_payout


def test_equal_split_no_fee():
    """Three participants with equal ratios split the pool evenly."""
    result = subsidy_payout(300.0, [1, 1, 1])
    assert len(result) == 3
    for payout in result:
        assert abs(payout - 100.0) < 1e-9


def test_weighted_split_no_fee():
    """Participants receive shares proportional to their ratios."""
    result = subsidy_payout(100.0, [1, 3])
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant receives the entire pool."""
    result = subsidy_payout(500.0, [5])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list must trigger a ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        subsidy_payout(100.0, [])


def test_negative_amount_raises():
    """A negative subsidy amount must not be accepted."""
    with pytest.raises(ValueError, match="negative amount"):
        subsidy_payout(-50.0, [1, 1])


def test_fee_deducted_from_total_pool():
    """The fee should be deducted once from the total pool, not per participant."""
    result = subsidy_payout(100.0, [1, 1], fee=20.0)
    total_distributed = sum(result)
    assert abs(total_distributed - 80.0) < 1e-9


def test_fee_equal_to_amount_yields_zero_payouts():
    """When the fee equals the pool, all payouts should be zero."""
    result = subsidy_payout(100.0, [1, 1, 1], fee=100.0)
    for payout in result:
        assert abs(payout - 0.0) < 1e-9


def test_fee_with_unequal_ratios():
    """Fee is deducted from the total pool before proportional splitting."""
    result = subsidy_payout(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9


def test_total_payouts_equal_amount_minus_fee():
    """Sum of all payouts must equal the pool after fee deduction."""
    result = subsidy_payout(1000.0, [2, 3, 5], fee=50.0)
    assert abs(sum(result) - 950.0) < 1e-9


def test_fee_exceeds_amount_gives_zero():
    """If the fee exceeds the pool, payouts should be clamped to zero."""
    result = subsidy_payout(30.0, [1, 2], fee=100.0)
    for payout in result:
        assert abs(payout - 0.0) < 1e-9
