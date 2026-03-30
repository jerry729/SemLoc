import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bump_refund import bump_refund
else:
    from programs.bump_refund import bump_refund


def test_first_refund_creates_entry():
    """A brand-new key should start at count 1 after the first bump."""
    counts = {}
    result = bump_refund(counts, "order_100")
    assert result == 1
    assert counts["order_100"] == 1


def test_increments_existing_count():
    """Bumping an existing key should increase its count by one."""
    counts = {"cust_42": 3}
    result = bump_refund(counts, "cust_42")
    assert result == 4
    assert counts["cust_42"] == 4


def test_no_ceiling_allows_unlimited_growth():
    """Without a max_value, the counter should grow without bound."""
    counts = {"k": 999}
    result = bump_refund(counts, "k")
    assert result == 1000


def test_multiple_keys_independent():
    """Bumping one key should not affect other keys in the mapping."""
    counts = {"a": 5, "b": 10}
    bump_refund(counts, "a")
    assert counts["b"] == 10
    assert counts["a"] == 6


def test_ceiling_clamps_at_max_value():
    """When the count reaches the ceiling, it should be clamped to max_value."""
    counts = {"order_1": 4}
    result = bump_refund(counts, "order_1", max_value=5)
    assert result == 5
    assert counts["order_1"] == 5


def test_repeated_bumps_stay_at_ceiling():
    """Repeated bumps past the ceiling should keep the count at max_value."""
    counts = {"order_2": 5}
    result = bump_refund(counts, "order_2", max_value=5)
    assert result == 5
    assert counts["order_2"] == 5


def test_ceiling_idempotent_after_saturation():
    """Bumping multiple times beyond ceiling should always return max_value."""
    counts = {"x": 10}
    for _ in range(5):
        result = bump_refund(counts, "x", max_value=10)
    assert result == 10
    assert counts["x"] == 10


def test_ceiling_reached_exactly_from_zero():
    """Starting from zero with max_value=1 should clamp to 1 on the first bump."""
    counts = {}
    result = bump_refund(counts, "single", max_value=1)
    assert result == 1
    assert counts["single"] == 1


def test_negative_max_value_raises():
    """A negative ceiling value should raise a ValueError."""
    counts = {}
    with pytest.raises(ValueError):
        bump_refund(counts, "bad", max_value=-3)


def test_counter_does_not_decrease_on_successive_ceiling_bumps():
    """The counter should never decrease when repeatedly bumped at the ceiling."""
    counts = {"z": 7}
    previous = 7
    for _ in range(10):
        current = bump_refund(counts, "z", max_value=8)
        assert current >= previous or current == 8
        previous = current
    assert counts["z"] == 8
