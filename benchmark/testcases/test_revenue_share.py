import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.revenue_share import revenue_share
else:
    from programs.revenue_share import revenue_share


def test_equal_split_no_fee():
    """Equal ratios should yield equal payouts summing to the total pool."""
    result = revenue_share(100.0, [1, 1, 1])
    for s in result:
        assert abs(s - 100.0 / 3) < 1e-9


def test_empty_ratios_raises():
    """Distribution requires at least one participant."""
    with pytest.raises(ValueError, match="ratios required"):
        revenue_share(100.0, [])


def test_negative_amount_raises():
    """A negative revenue pool is not permitted."""
    with pytest.raises(ValueError, match="negative amount"):
        revenue_share(-50.0, [1, 2])


def test_zero_amount_no_fee():
    """A zero pool should distribute zero to each participant."""
    result = revenue_share(0.0, [3, 7])
    assert all(abs(s) < 1e-9 for s in result)


def test_single_participant_no_fee():
    """A single participant should receive the entire pool."""
    result = revenue_share(250.0, [5])
    assert abs(result[0] - 250.0) < 1e-9


def test_fee_deducted_before_split_total():
    """Platform fee should reduce the total distributed amount."""
    result = revenue_share(100.0, [1, 1], fee=20.0)
    total_paid = sum(result)
    assert abs(total_paid - 80.0) < 1e-9


def test_fee_deducted_per_participant_equal():
    """With equal ratios and a fee, each participant receives (amount - fee) / n."""
    result = revenue_share(200.0, [1, 1], fee=40.0)
    assert abs(result[0] - 80.0) < 1e-9
    assert abs(result[1] - 80.0) < 1e-9


def test_fee_larger_than_amount_yields_zero():
    """When the fee exceeds the pool, all payouts should be zero."""
    result = revenue_share(10.0, [1, 1, 1], fee=50.0)
    for s in result:
        assert abs(s) < 1e-9


def test_weighted_split_with_fee():
    """Unequal ratios with a fee should produce proportional shares of the net pool."""
    result = revenue_share(1000.0, [3, 7], fee=100.0)
    assert abs(result[0] - 270.0) < 1e-9
    assert abs(result[1] - 630.0) < 1e-9


def test_three_way_split_with_fee_sums_correctly():
    """Total payouts after fee deduction should equal pool minus fee."""
    result = revenue_share(500.0, [2, 3, 5], fee=50.0)
    assert abs(sum(result) - 450.0) < 1e-9
