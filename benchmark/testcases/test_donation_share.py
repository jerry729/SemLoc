import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.donation_share import donation_share
else:
    from programs.donation_share import donation_share


def test_equal_split_no_fee():
    """Equal ratios should distribute the donation evenly among all recipients."""
    result = donation_share(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for payout in result:
        assert abs(payout - 25.0) < 1e-9


def test_single_recipient_no_fee():
    """A single recipient receives the entire donation when there is no fee."""
    result = donation_share(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_weighted_ratios_no_fee():
    """Recipients with different ratios should receive proportional shares."""
    result = donation_share(100.0, [1, 3])
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero donation should yield zero payouts for all participants."""
    result = donation_share(0.0, [1, 2, 3])
    assert all(abs(p) < 1e-9 for p in result)


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="empty ratios"):
        donation_share(100.0, [])


def test_total_payouts_equal_net_amount_with_fee():
    """The sum of all payouts should equal the donation minus the processing fee."""
    result = donation_share(200.0, [1, 1], fee=20.0)
    total_paid = sum(result)
    assert abs(total_paid - 180.0) < 1e-9


def test_fee_deducted_before_split_equal_ratios():
    """With equal ratios, each payout should be (amount - fee) / n."""
    result = donation_share(100.0, [1, 1], fee=10.0)
    assert abs(result[0] - 45.0) < 1e-9
    assert abs(result[1] - 45.0) < 1e-9


def test_fee_deducted_proportionally_unequal_ratios():
    """Fee is deducted from the gross amount before proportional splitting."""
    result = donation_share(100.0, [1, 3], fee=20.0)
    expected_net = 80.0
    assert abs(result[0] - expected_net * 0.25) < 1e-9
    assert abs(result[1] - expected_net * 0.75) < 1e-9


def test_large_fee_caps_at_zero():
    """A fee exceeding the donation amount should yield zero payouts, not negative."""
    result = donation_share(10.0, [1, 1], fee=50.0)
    assert all(abs(p) < 1e-9 for p in result)


def test_fee_single_recipient():
    """A single recipient should receive the donation minus the fee."""
    result = donation_share(1000.0, [5], fee=100.0)
    assert abs(result[0] - 900.0) < 1e-9
