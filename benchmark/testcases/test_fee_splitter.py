import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.fee_splitter import fee_splitter
else:
    from programs.fee_splitter import fee_splitter


def test_equal_split_no_fee():
    """Equal ratios with no fee should yield equal payouts summing to the full amount."""
    result = fee_splitter(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for r in result:
        assert abs(r - 25.0) < 1e-9


def test_empty_ratios_raises():
    """An empty participant list must raise ValueError."""
    with pytest.raises(ValueError, match="empty ratios"):
        fee_splitter(100.0, [])


def test_negative_amount_raises():
    """Negative amounts are not allowed."""
    with pytest.raises(ValueError, match="negative amount"):
        fee_splitter(-50.0, [1, 2])


def test_zero_amount_no_fee():
    """Zero amount with no fee should yield all-zero payouts."""
    result = fee_splitter(0.0, [3, 7])
    assert all(abs(r) < 1e-9 for r in result)


def test_weighted_split_no_fee():
    """Unequal ratios should produce proportional payouts when fee is zero."""
    result = fee_splitter(200.0, [1, 3])
    assert abs(result[0] - 50.0) < 1e-9
    assert abs(result[1] - 150.0) < 1e-9


def test_total_payout_equals_amount_minus_fee():
    """The total distributed should equal the original amount minus the platform fee."""
    result = fee_splitter(1000.0, [1, 1], fee=100.0)
    total = sum(result)
    assert abs(total - 900.0) < 1e-9


def test_fee_deducted_once_not_per_participant():
    """The fee is a single flat deduction, not applied to each participant separately."""
    result = fee_splitter(100.0, [1, 1, 1], fee=30.0)
    total = sum(result)
    assert abs(total - 70.0) < 1e-9


def test_single_participant_with_fee():
    """A single participant receives the full amount less the platform fee."""
    result = fee_splitter(500.0, [1], fee=50.0)
    assert len(result) == 1
    assert abs(result[0] - 450.0) < 1e-9


def test_fee_larger_than_amount_clamps_to_zero():
    """When the fee exceeds the amount, payouts should be clamped at zero."""
    result = fee_splitter(10.0, [1, 1], fee=50.0)
    for r in result:
        assert r >= 0.0
    assert abs(sum(result)) < 1e-9


def test_three_way_split_with_fee():
    """A three-way split with a fee should distribute the net amount proportionally."""
    result = fee_splitter(300.0, [1, 2, 3], fee=60.0)
    net = 300.0 - 60.0
    assert abs(result[0] - net * (1 / 6)) < 1e-9
    assert abs(result[1] - net * (2 / 6)) < 1e-9
    assert abs(result[2] - net * (3 / 6)) < 1e-9
