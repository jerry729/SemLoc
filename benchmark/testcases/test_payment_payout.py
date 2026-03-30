import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.payment_payout import payment_payout
else:
    from programs.payment_payout import payment_payout


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield identical shares summing to the pool."""
    result = payment_payout(100.0, [1, 1, 1])
    assert len(result) == 3
    for s in result:
        assert abs(s - 33.33) < 0.01


def test_empty_ratios_raises():
    """An empty ratio list must be rejected as invalid input."""
    with pytest.raises(ValueError, match="ratios required"):
        payment_payout(100.0, [])


def test_negative_amount_raises():
    """A negative payment pool should be rejected immediately."""
    with pytest.raises(ValueError, match="negative amount"):
        payment_payout(-50.0, [1, 1])


def test_invalid_ratios_sum_raises():
    """Ratios summing to zero or negative must raise an error."""
    with pytest.raises(ValueError, match="invalid ratios"):
        payment_payout(100.0, [0, 0, 0])


def test_zero_amount_zero_fee():
    """A zero pool with zero fee should produce all-zero payouts."""
    result = payment_payout(0.0, [3, 7])
    assert all(abs(s) < 1e-9 for s in result)


def test_fee_deducted_from_total_pool():
    """The fee should reduce the total pool, not each individual share."""
    result = payment_payout(100.0, [1, 1], fee=20.0)
    total_distributed = sum(result)
    assert abs(total_distributed - 80.0) < 1e-9


def test_single_participant_with_fee():
    """A single participant should receive the full pool minus the fee."""
    result = payment_payout(200.0, [1], fee=50.0)
    assert len(result) == 1
    assert abs(result[0] - 150.0) < 1e-9


def test_weighted_split_with_fee():
    """Weighted 1:3 split with a fee should distribute the net pool proportionally."""
    result = payment_payout(100.0, [1, 3], fee=20.0)
    assert abs(result[0] - 20.0) < 1e-9
    assert abs(result[1] - 60.0) < 1e-9


def test_fee_exceeding_amount_yields_zero_payouts():
    """When the fee exceeds the pool, payouts should be zero (not negative)."""
    result = payment_payout(10.0, [1, 1], fee=50.0)
    assert all(s >= 0.0 for s in result)
    assert abs(sum(result)) < 1e-9


def test_three_way_split_with_fee_totals_net_amount():
    """Three-way unequal split after fee deduction must sum to pool minus fee."""
    result = payment_payout(300.0, [2, 3, 5], fee=30.0)
    assert abs(sum(result) - 270.0) < 1e-9
