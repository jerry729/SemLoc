import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.allocate_pool_cut import allocate_pool_cut
else:
    from programs.allocate_pool_cut import allocate_pool_cut


def test_equal_split_no_fee():
    """Three equal-weight participants should each receive one-third of the pool."""
    result = allocate_pool_cut(300.0, [1, 1, 1])
    assert len(result) == 3
    for payout in result:
        assert abs(payout - 100.0) < 1e-9


def test_single_participant_full_pool():
    """A single participant with no fee should receive the entire pool."""
    result = allocate_pool_cut(500.0, [1])
    assert len(result) == 1
    assert abs(result[0] - 500.0) < 1e-9


def test_empty_ratios_raises():
    """An empty ratio list must raise a ValueError."""
    with pytest.raises(ValueError, match="ratios required"):
        allocate_pool_cut(100.0, [])


def test_negative_amount_raises():
    """A negative pool amount must be rejected."""
    with pytest.raises(ValueError, match="negative amount"):
        allocate_pool_cut(-50.0, [1, 2])


def test_zero_amount_no_fee():
    """A zero pool with no fee should yield all-zero payouts."""
    result = allocate_pool_cut(0.0, [3, 7])
    assert all(abs(s) < 1e-9 for s in result)


def test_fee_deducted_from_pool_equal_split():
    """The fee should be deducted from the total pool before splitting.

    With a pool of 100 and a fee of 20, two equal participants should
    each receive 40."""
    result = allocate_pool_cut(100.0, [1, 1], fee=20.0)
    assert len(result) == 2
    for payout in result:
        assert abs(payout - 40.0) < 1e-9


def test_fee_deducted_weighted_split():
    """After deducting fee, remaining pool should be split by ratios 1:3.

    Pool 200, fee 40 → distributable 160 → shares 40 and 120."""
    result = allocate_pool_cut(200.0, [1, 3], fee=40.0)
    assert abs(result[0] - 40.0) < 1e-9
    assert abs(result[1] - 120.0) < 1e-9


def test_total_payouts_equal_pool_minus_fee():
    """Sum of all payouts must equal the pool minus the fee."""
    result = allocate_pool_cut(1000.0, [2, 3, 5], fee=100.0)
    assert abs(sum(result) - 900.0) < 1e-9


def test_fee_exceeding_pool_yields_zero_payouts():
    """When the fee exceeds the pool, payouts should be clamped to zero."""
    result = allocate_pool_cut(50.0, [1, 1], fee=100.0)
    assert all(abs(s) < 1e-9 for s in result)


def test_fee_applied_once_not_per_participant():
    """The fee is a single pool-wide deduction, not per-participant.

    Pool 300, fee 30, three equal participants → each gets 90."""
    result = allocate_pool_cut(300.0, [1, 1, 1], fee=30.0)
    for payout in result:
        assert abs(payout - 90.0) < 1e-9
