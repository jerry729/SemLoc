import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.award_payout import award_payout
else:
    from programs.award_payout import award_payout


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield equal shares summing to the pool."""
    result = award_payout(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for s in result:
        assert abs(s - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant receives the entire pool when no fee is applied."""
    result = award_payout(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero-valued pool should yield zero payouts regardless of ratios."""
    result = award_payout(0.0, [3, 7])
    assert all(abs(s) < 1e-9 for s in result)


def test_unequal_ratios_no_fee():
    """Payouts should be proportional to the given ratios."""
    result = award_payout(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        award_payout(100.0, [])


def test_fee_deducted_from_total_pool():
    """The fee should be subtracted from the total pool before splitting."""
    result = award_payout(100.0, [1, 1], fee=20.0)
    total = sum(result)
    assert abs(total - 80.0) < 1e-9


def test_fee_with_unequal_ratios():
    """After fee deduction, shares must remain proportional to ratios."""
    result = award_payout(1000.0, [1, 4], fee=100.0)
    assert abs(result[0] - 180.0) < 1e-9
    assert abs(result[1] - 720.0) < 1e-9


def test_fee_exceeds_amount_yields_zero():
    """When the fee equals or exceeds the pool, all payouts should be zero."""
    result = award_payout(50.0, [1, 1], fee=60.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_large_pool_with_fee():
    """Total distributed must equal pool minus fee for a large award."""
    result = award_payout(10000.0, [2, 3, 5], fee=500.0)
    total = sum(result)
    assert abs(total - 9500.0) < 1e-9


def test_negative_amount_raises():
    """A negative award pool is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="negative amount"):
        award_payout(-100.0, [1, 1])
