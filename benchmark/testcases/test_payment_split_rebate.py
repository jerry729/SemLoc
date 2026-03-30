import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.payment_split_rebate import payment_split_rebate
else:
    from programs.payment_split_rebate import payment_split_rebate


def test_equal_split_no_rebate():
    """Equal ratios with zero rebate should yield identical payouts summing to total."""
    result = payment_split_rebate(100.0, [1, 1, 1])
    assert len(result) == 3
    for s in result:
        assert abs(s - 100.0 / 3) < 1e-9


def test_single_participant_no_rebate():
    """A single participant receives the entire payment when rebate is zero."""
    result = payment_split_rebate(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_negative_total_raises():
    """A negative gross payment should be rejected immediately."""
    with pytest.raises(ValueError, match="negative total"):
        payment_split_rebate(-10.0, [1, 2])


def test_empty_ratios_raises():
    """An empty ratios list is invalid and must raise."""
    with pytest.raises(ValueError, match="invalid ratios"):
        payment_split_rebate(100.0, [])


def test_unequal_ratios_no_rebate():
    """Unequal ratios should produce proportional shares summing to total."""
    result = payment_split_rebate(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_rebate_subtracted_from_pool_equal_split():
    """Rebate must reduce the distributed pool; equal-split payouts should reflect the reduced total."""
    result = payment_split_rebate(100.0, [1, 1], rebate=20.0)
    assert len(result) == 2
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_rebate_total_payout_sum():
    """The sum of all payouts should equal total minus the rebate."""
    result = payment_split_rebate(1000.0, [2, 3, 5], rebate=100.0)
    assert abs(sum(result) - 900.0) < 1e-9


def test_rebate_with_single_participant():
    """A single participant's payout must equal the total minus the rebate."""
    result = payment_split_rebate(300.0, [1], rebate=50.0)
    assert abs(result[0] - 250.0) < 1e-9


def test_rebate_exceeding_total_clamps_to_zero():
    """When the rebate exceeds the total, all payouts should be zero (clamped)."""
    result = payment_split_rebate(10.0, [1, 1], rebate=50.0)
    for s in result:
        assert abs(s - 0.0) < 1e-9


def test_rebate_proportional_distribution():
    """With a rebate applied, shares should remain proportional to the original ratios."""
    result = payment_split_rebate(200.0, [1, 3], rebate=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9
