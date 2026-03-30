import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.rebate_splitter import rebate_splitter
else:
    from programs.rebate_splitter import rebate_splitter


def test_equal_split_no_fee():
    """Equal ratios should produce equal shares summing to the total amount."""
    result = rebate_splitter(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for share in result:
        assert abs(share - 25.0) < 1e-9


def test_single_recipient_no_fee():
    """A single recipient receives the entire rebate when no fee is charged."""
    result = rebate_splitter(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_zero_amount_no_fee():
    """A zero rebate amount should yield zero payouts for all recipients."""
    result = rebate_splitter(0.0, [3, 7])
    assert all(abs(s) < 1e-9 for s in result)


def test_weighted_ratios_no_fee():
    """Payouts should be proportional to the provided ratio weights."""
    result = rebate_splitter(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="no ratios"):
        rebate_splitter(100.0, [])


def test_fee_deducted_total_equals_amount_minus_fee():
    """The sum of all payouts should equal the original amount minus the fee."""
    result = rebate_splitter(100.0, [1, 1], fee=20.0)
    total = sum(result)
    assert abs(total - 80.0) < 1e-9


def test_fee_distributed_equally_among_equal_ratios():
    """With equal ratios, each recipient share should be (amount - fee) / n."""
    result = rebate_splitter(100.0, [1, 1, 1, 1], fee=40.0)
    for share in result:
        assert abs(share - 15.0) < 1e-9


def test_fee_with_weighted_ratios():
    """Fee should be deducted from the total before proportional splitting."""
    result = rebate_splitter(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9


def test_fee_exceeds_amount_payouts_are_zero():
    """When the fee exceeds the amount, all payouts should be clamped to zero."""
    result = rebate_splitter(10.0, [1, 1], fee=50.0)
    for share in result:
        assert abs(share) < 1e-9


def test_large_fee_single_recipient():
    """A single recipient should receive max(0, amount - fee)."""
    result = rebate_splitter(100.0, [5], fee=100.0)
    assert abs(result[0]) < 1e-9
