import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.rent_splitter import rent_splitter
else:
    from programs.rent_splitter import rent_splitter


def test_equal_split_no_fee():
    """Three equal tenants splitting 900 should each pay 300."""
    result = rent_splitter(900.0, [1, 1, 1])
    assert all(abs(s - 300.0) < 1e-9 for s in result)


def test_weighted_split_no_fee():
    """Two tenants with 2:1 ratio splitting 300 should get 200 and 100."""
    result = rent_splitter(300.0, [2, 1])
    assert abs(result[0] - 200.0) < 1e-9
    assert abs(result[1] - 100.0) < 1e-9


def test_zero_amount_no_fee():
    """Splitting zero rent should yield zero shares for everyone."""
    result = rent_splitter(0.0, [1, 2, 3])
    assert all(abs(s) < 1e-9 for s in result)


def test_single_participant_no_fee():
    """A single tenant pays the entire amount."""
    result = rent_splitter(1500.0, [5])
    assert abs(result[0] - 1500.0) < 1e-9


def test_raises_on_empty_ratios():
    """An empty ratios list is invalid and should raise."""
    with pytest.raises(ValueError, match="no ratios"):
        rent_splitter(100.0, [])


def test_total_shares_equal_amount_after_fee():
    """Sum of all shares must equal the original amount minus the fee."""
    result = rent_splitter(1000.0, [1, 1, 1, 1], fee=200.0)
    assert abs(sum(result) - 800.0) < 1e-9


def test_fee_deducted_once_from_total():
    """The fee should be deducted once from the total, not per-participant."""
    result = rent_splitter(1000.0, [1, 1], fee=100.0)
    assert abs(result[0] - 450.0) < 1e-9
    assert abs(result[1] - 450.0) < 1e-9


def test_fee_with_unequal_ratios():
    """After fee deduction, remaining amount is split proportionally."""
    result = rent_splitter(500.0, [3, 2], fee=50.0)
    assert abs(result[0] - 270.0) < 1e-9
    assert abs(result[1] - 180.0) < 1e-9


def test_fee_equal_to_amount_yields_zero_shares():
    """When the fee equals the total, all participants should receive zero."""
    result = rent_splitter(100.0, [1, 1], fee=100.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_large_fee_does_not_produce_negative_shares():
    """Shares must never go below zero even when the fee exceeds the amount."""
    result = rent_splitter(50.0, [1, 1, 1], fee=200.0)
    assert all(s >= 0.0 for s in result)
