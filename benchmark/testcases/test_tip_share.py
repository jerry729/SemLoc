import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.tip_share import tip_share
else:
    from programs.tip_share import tip_share


def test_equal_split_no_fee():
    """Equal ratios with no fee should divide the tip evenly."""
    result = tip_share(30.0, [1, 1, 1])
    assert all(abs(s - 10.0) < 1e-9 for s in result)


def test_single_recipient_no_fee():
    """A single recipient receives the full tip when there is no fee."""
    result = tip_share(50.0, [1])
    assert abs(result[0] - 50.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero tip should yield zero payouts for every recipient."""
    result = tip_share(0.0, [1, 2, 3])
    assert all(abs(s) < 1e-9 for s in result)


def test_weighted_split_no_fee():
    """Unequal ratios should produce proportional shares."""
    result = tip_share(100.0, [1, 3])
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list is not a valid distribution."""
    with pytest.raises(ValueError, match="no ratios"):
        tip_share(10.0, [])


def test_fee_deducted_from_total_equal_split():
    """The fee should be subtracted from the total before splitting equally."""
    result = tip_share(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_deducted_single_recipient():
    """A single recipient should receive the tip minus the fee."""
    result = tip_share(100.0, [1], fee=10.0)
    assert abs(result[0] - 90.0) < 1e-9


def test_fee_larger_than_amount_floors_to_zero():
    """When the fee exceeds the tip, no recipient should receive a negative payout."""
    result = tip_share(5.0, [1, 1], fee=10.0)
    assert all(s >= 0.0 for s in result)
    assert abs(sum(result)) < 1e-9


def test_total_payout_equals_amount_minus_fee():
    """The sum of all payouts must equal the tip amount minus the fee."""
    result = tip_share(200.0, [3, 2, 5], fee=50.0)
    assert abs(sum(result) - 150.0) < 1e-9


def test_fee_with_weighted_ratios():
    """Weighted ratios should still yield proportional shares after fee deduction."""
    result = tip_share(100.0, [1, 3], fee=20.0)
    assert abs(result[0] - 20.0) < 1e-9
    assert abs(result[1] - 60.0) < 1e-9
