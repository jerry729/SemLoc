import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.credit_share import credit_share
else:
    from programs.credit_share import credit_share


def test_equal_split_no_fee():
    """Equal ratios with no fee should produce identical shares summing to the amount."""
    result = credit_share(100.0, [1, 1, 1, 1])
    assert len(result) == 4
    for s in result:
        assert abs(s - 25.0) < 1e-9


def test_single_participant_no_fee():
    """A single participant should receive the entire pool when there is no fee."""
    result = credit_share(500.0, [3])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_weighted_split_no_fee():
    """Shares should be proportional to given ratios without a fee."""
    result = credit_share(100.0, [1, 3])
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list must be rejected."""
    with pytest.raises(ValueError, match="ratios required"):
        credit_share(100.0, [])


def test_negative_amount_raises():
    """A negative credit pool must be rejected."""
    with pytest.raises(ValueError, match="negative amount"):
        credit_share(-10.0, [1, 2])


def test_fee_deducted_from_total_pool():
    """The fee should be deducted from the total pool before splitting among participants."""
    result = credit_share(100.0, [1, 1], fee=20.0)
    assert abs(sum(result) - 80.0) < 1e-9
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 40.0) < 1e-9


def test_fee_with_unequal_ratios():
    """Fee deduction should happen before proportional splitting with unequal weights."""
    result = credit_share(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9


def test_fee_equal_to_amount_yields_zero():
    """When the fee equals the amount, all shares should be zero."""
    result = credit_share(50.0, [2, 3], fee=50.0)
    for s in result:
        assert abs(s) < 1e-9


def test_fee_exceeding_amount_clamps_to_zero():
    """When the fee exceeds the pool, shares should be clamped to zero rather than going negative."""
    result = credit_share(30.0, [1, 1, 1], fee=100.0)
    for s in result:
        assert abs(s) < 1e-9


def test_total_payout_matches_pool_minus_fee():
    """The sum of all shares must equal the pool minus the fee for a variety of ratios."""
    result = credit_share(1000.0, [5, 3, 2], fee=100.0)
    assert abs(sum(result) - 900.0) < 1e-9
