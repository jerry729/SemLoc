import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.divide_refund import divide_refund
else:
    from programs.divide_refund import divide_refund


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield equal payouts summing to the total."""
    result = divide_refund(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for payout in result:
        assert abs(payout - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant receives the full refund when no fee is applied."""
    result = divide_refund(200.0, [5])
    assert len(result) == 1
    assert abs(result[0] - 200.0) < 1e-9


def test_weighted_split_no_fee():
    """Payouts should reflect the weight ratios when no fee is present."""
    result = divide_refund(300.0, [1, 2])
    assert abs(result[0] - 100.0) < 1e-9
    assert abs(result[1] - 200.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero refund amount with no fee produces all zero payouts."""
    result = divide_refund(0.0, [1, 2, 3])
    for p in result:
        assert abs(p) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list is invalid and should raise ValueError."""
    with pytest.raises(ValueError, match="empty ratios"):
        divide_refund(100.0, [])


def test_fee_deducted_from_total_equal_split():
    """The processing fee should be subtracted from the total before splitting evenly."""
    result = divide_refund(100.0, [1, 1], fee=20.0)
    assert len(result) == 2
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_deducted_total_payouts_sum():
    """Sum of payouts should equal the amount minus the fee."""
    result = divide_refund(500.0, [3, 2, 5], fee=50.0)
    expected_total = 450.0
    assert abs(sum(result) - expected_total) < 1e-9


def test_fee_with_weighted_ratios():
    """Weighted payouts after fee deduction should match proportional shares of the net amount."""
    result = divide_refund(1000.0, [1, 3], fee=200.0)
    net = 800.0
    assert abs(result[0] - net * 0.25) < 1e-9
    assert abs(result[1] - net * 0.75) < 1e-9


def test_fee_exceeds_amount_yields_zero():
    """When the fee equals or exceeds the amount, all payouts should be zero."""
    result = divide_refund(50.0, [1, 1], fee=50.0)
    for p in result:
        assert abs(p) < 1e-9


def test_single_participant_with_fee():
    """A single participant receives the full net amount after fee."""
    result = divide_refund(100.0, [1], fee=10.0)
    assert abs(result[0] - 90.0) < 1e-9
