import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.divide_coupon import divide_coupon
else:
    from programs.divide_coupon import divide_coupon


def test_equal_ratios_no_fee():
    """Equal ratios without fee should split the amount equally."""
    result = divide_coupon(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for payout in result:
        assert abs(payout - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant receives the full coupon amount when no fee applies."""
    result = divide_coupon(200.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 200.0) < 1e-9


def test_weighted_ratios_no_fee():
    """Payouts should be proportional to the given ratios."""
    result = divide_coupon(100.0, [1, 3])
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero coupon should yield zero payouts for all participants."""
    result = divide_coupon(0.0, [2, 3, 5])
    for payout in result:
        assert abs(payout) < 1e-9


def test_empty_ratios_raises():
    """An empty ratios list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="empty ratios"):
        divide_coupon(100.0, [])


def test_total_payout_equals_amount_minus_fee():
    """The sum of all payouts should equal the original amount minus the fee."""
    result = divide_coupon(100.0, [1, 1], fee=10.0)
    total = sum(result)
    assert abs(total - 90.0) < 1e-9


def test_fee_deducted_before_distribution_equal_split():
    """With equal ratios, each participant should receive (amount - fee) / n."""
    result = divide_coupon(100.0, [1, 1, 1], fee=30.0)
    expected_each = (100.0 - 30.0) / 3.0
    for payout in result:
        assert abs(payout - expected_each) < 1e-9


def test_fee_deducted_with_unequal_ratios():
    """Fee should reduce the total pool before proportional distribution."""
    result = divide_coupon(200.0, [1, 3], fee=40.0)
    net = 200.0 - 40.0
    assert abs(result[0] - net * 0.25) < 1e-9
    assert abs(result[1] - net * 0.75) < 1e-9


def test_fee_exceeding_amount_clamps_to_zero():
    """When the fee exceeds the amount, payouts should be zero (clamped)."""
    result = divide_coupon(10.0, [1, 1], fee=50.0)
    for payout in result:
        assert abs(payout) < 1e-9


def test_negative_amount_raises():
    """A negative coupon amount is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="negative amount"):
        divide_coupon(-5.0, [1, 2])
