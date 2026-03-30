import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bill_payout import bill_payout
else:
    from programs.bill_payout import bill_payout


def test_equal_split_no_fee():
    """Equal ratios without any fee should yield identical shares summing to the amount."""
    result = bill_payout(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for s in result:
        assert abs(s - 25.0) < 1e-9
    assert abs(sum(result) - 100.0) < 1e-9


def test_unequal_ratios_no_fee():
    """Unequal ratios should distribute the amount proportionally."""
    result = bill_payout(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero amount should give all participants zero shares."""
    result = bill_payout(0.0, [5, 10])
    assert all(abs(s) < 1e-9 for s in result)


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        bill_payout(100.0, [])


def test_negative_amount_raises():
    """Negative pool amounts are not allowed."""
    with pytest.raises(ValueError, match="negative amount"):
        bill_payout(-50.0, [1, 1])


def test_fee_deducted_from_total_pool():
    """The fee should be deducted from the total pool before splitting among participants."""
    result = bill_payout(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_equal_to_amount_yields_zero_shares():
    """When the fee equals the total amount, all payouts should be zero."""
    result = bill_payout(50.0, [1, 2, 3], fee=50.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_fee_with_unequal_ratios():
    """After fee deduction, unequal ratios should split the remaining pool correctly."""
    result = bill_payout(100.0, [1, 3], fee=20.0)
    assert abs(result[0] - 20.0) < 1e-9
    assert abs(result[1] - 60.0) < 1e-9


def test_shares_sum_equals_net_amount():
    """The sum of all shares must equal the amount minus the fee."""
    result = bill_payout(300.0, [2, 3, 5], fee=30.0)
    assert abs(sum(result) - 270.0) < 1e-9


def test_single_participant_with_fee():
    """A single participant should receive the full pool minus the fee."""
    result = bill_payout(100.0, [1], fee=10.0)
    assert len(result) == 1
    assert abs(result[0] - 90.0) < 1e-9
