import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.grant_share import grant_share
else:
    from programs.grant_share import grant_share


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield identical payouts summing to the total amount."""
    result = grant_share(100.0, [1, 1, 1])
    assert len(result) == 3
    for payout in result:
        assert abs(payout - 100.0 / 3) < 1e-9


def test_single_recipient_no_fee():
    """A single recipient with no fee receives the full grant amount."""
    result = grant_share(250.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 250.0) < 1e-9


def test_weighted_split_no_fee():
    """Recipients with different ratios should receive proportional payouts."""
    result = grant_share(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_zero_amount_with_fee():
    """A zero grant amount with a fee should yield zero payouts (not negative)."""
    result = grant_share(0.0, [1, 1], fee=10.0)
    for payout in result:
        assert payout >= 0.0


def test_empty_ratios_raises():
    """Providing an empty ratios list must raise a ValueError."""
    with pytest.raises(ValueError, match="no ratios"):
        grant_share(100.0, [])


def test_fee_deducted_from_total_two_equal():
    """The fee should be deducted from the total pool, then the remainder split equally."""
    result = grant_share(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_deducted_single_recipient():
    """A single recipient should receive the amount minus the fee."""
    result = grant_share(500.0, [1], fee=50.0)
    assert abs(result[0] - 450.0) < 1e-9


def test_total_payout_equals_amount_minus_fee():
    """Sum of all payouts must equal the grant amount minus the fee."""
    result = grant_share(1000.0, [2, 3, 5], fee=100.0)
    assert abs(sum(result) - 900.0) < 1e-9


def test_fee_with_unequal_ratios():
    """Proportional distribution after fee deduction should preserve ratio relationships."""
    result = grant_share(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9


def test_negative_amount_raises():
    """A negative grant amount must raise a ValueError."""
    with pytest.raises(ValueError, match="negative amount"):
        grant_share(-10.0, [1, 1])
