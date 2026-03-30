import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.storage_quota_split import storage_quota_split
else:
    from programs.storage_quota_split import storage_quota_split


def test_equal_split_no_fee():
    """Equal ratios with no fee should divide the total evenly."""
    result = storage_quota_split(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for s in result:
        assert abs(s - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant receives the entire quota when no fee is applied."""
    result = storage_quota_split(500.0, [3])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_negative_total_raises():
    """Negative totals are rejected immediately."""
    with pytest.raises(ValueError, match="negative total"):
        storage_quota_split(-10.0, [1, 1])


def test_empty_ratios_raises():
    """An empty ratio list is invalid and must raise."""
    with pytest.raises(ValueError, match="invalid ratios"):
        storage_quota_split(100.0, [])


def test_zero_total_no_fee():
    """Zero total with valid ratios should yield all-zero shares."""
    result = storage_quota_split(0.0, [1, 2, 3])
    assert all(abs(s) < 1e-9 for s in result)


def test_fee_deducted_from_pool_two_equal_participants():
    """The fee should be deducted once from the total pool before splitting."""
    result = storage_quota_split(100.0, [1, 1], fee=20.0)
    assert len(result) == 2
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_deducted_shares_sum_equals_total_minus_fee():
    """Sum of all shares must equal total minus the fee."""
    result = storage_quota_split(200.0, [1, 3], fee=50.0)
    assert abs(sum(result) - 150.0) < 1e-9


def test_fee_with_unequal_ratios():
    """Shares should reflect proportional allocation of (total - fee)."""
    result = storage_quota_split(1000.0, [1, 4], fee=100.0)
    assert abs(result[0] - 180.0) < 1e-9
    assert abs(result[1] - 720.0) < 1e-9


def test_fee_equal_to_total():
    """When the fee equals the total, every participant receives zero."""
    result = storage_quota_split(50.0, [2, 3], fee=50.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_large_fee_clamped_to_zero_pool():
    """A fee exceeding the total should still result in non-negative shares."""
    result = storage_quota_split(30.0, [1, 1, 1], fee=100.0)
    assert all(s >= -1e-9 for s in result)
    assert abs(sum(result)) < 1e-9
