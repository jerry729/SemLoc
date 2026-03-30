import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.allocate_bounty_cut import allocate_bounty_cut
else:
    from programs.allocate_bounty_cut import allocate_bounty_cut


def test_equal_split_no_fee():
    """Three equal contributors sharing a bounty should each receive one third."""
    result = allocate_bounty_cut(300.0, [1, 1, 1])
    assert len(result) == 3
    for payout in result:
        assert abs(payout - 100.0) < 1e-9


def test_weighted_split_no_fee():
    """Payouts should be proportional to each participant's ratio."""
    result = allocate_bounty_cut(100.0, [1, 3])
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_single_recipient_no_fee():
    """A single recipient with no fee should receive the entire bounty."""
    result = allocate_bounty_cut(500.0, [5])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_zero_amount_no_fee():
    """When the bounty is zero, every payout should be zero."""
    result = allocate_bounty_cut(0.0, [1, 2, 3])
    for payout in result:
        assert abs(payout) < 1e-9


def test_empty_ratios_raises():
    """An empty list of ratios is not a valid allocation request."""
    with pytest.raises(ValueError, match="no ratios"):
        allocate_bounty_cut(100.0, [])


def test_total_payout_equals_bounty_after_fee():
    """Sum of all payouts should equal the bounty minus the platform fee."""
    result = allocate_bounty_cut(1000.0, [1, 1, 1, 1], fee=200.0)
    total = sum(result)
    assert abs(total - 800.0) < 1e-9


def test_fee_deducted_before_splitting_two_recipients():
    """With two equal recipients and a fee, each receives half of the net amount."""
    result = allocate_bounty_cut(100.0, [1, 1], fee=20.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_larger_than_amount_yields_zero():
    """If the fee exceeds the bounty, payouts should be clamped to zero."""
    result = allocate_bounty_cut(50.0, [1, 1], fee=100.0)
    for payout in result:
        assert abs(payout) < 1e-9


def test_unequal_ratios_with_fee():
    """Fee is deducted once from the pool, then the remainder is split proportionally."""
    result = allocate_bounty_cut(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9


def test_negative_amount_raises():
    """A negative bounty amount is invalid and must raise an error."""
    with pytest.raises(ValueError, match="negative amount"):
        allocate_bounty_cut(-100.0, [1, 2])
