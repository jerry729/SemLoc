import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.royalty_payout import royalty_payout
else:
    from programs.royalty_payout import royalty_payout


def test_equal_split_no_fee():
    """Equal ratios with no fee should produce identical payouts that sum to the pool."""
    result = royalty_payout(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for s in result:
        assert abs(s - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A sole participant receives the entire pool when there is no fee."""
    result = royalty_payout(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        royalty_payout(100.0, [])


def test_negative_amount_raises():
    """A negative pool amount is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="negative amount"):
        royalty_payout(-10.0, [1, 2])


def test_weighted_split_no_fee():
    """Unequal ratios should produce proportional payouts summing to the pool."""
    result = royalty_payout(120.0, [1, 2, 3])
    assert abs(result[0] - 20.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9
    assert abs(result[2] - 60.0) < 1e-9


def test_fee_deducted_from_pool_total():
    """The processing fee should be deducted once from the total pool, not per participant."""
    result = royalty_payout(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9


def test_fee_equal_split():
    """With equal ratios and a fee, each share equals (amount - fee) / n."""
    result = royalty_payout(200.0, [1, 1, 1, 1], fee=40.0)
    expected_each = 40.0
    for s in result:
        assert abs(s - expected_each) < 1e-9


def test_fee_exceeding_amount_clamps_to_zero():
    """When the fee exceeds the pool, all payouts should be zero (non-negative)."""
    result = royalty_payout(10.0, [1, 2, 3], fee=50.0)
    for s in result:
        assert abs(s - 0.0) < 1e-9


def test_fee_with_unequal_ratios():
    """Fee-adjusted pool should still be split proportionally by ratios."""
    result = royalty_payout(100.0, [1, 3], fee=20.0)
    assert abs(result[0] - 20.0) < 1e-9
    assert abs(result[1] - 60.0) < 1e-9


def test_zero_amount_with_fee():
    """A zero pool with a fee should produce all-zero payouts."""
    result = royalty_payout(0.0, [5, 5], fee=10.0)
    for s in result:
        assert abs(s - 0.0) < 1e-9
