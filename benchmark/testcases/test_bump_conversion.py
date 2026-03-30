import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bump_conversion import bump_conversion
else:
    from programs.bump_conversion import bump_conversion


def test_first_conversion_from_empty_counters():
    """A new key should start at zero and be bumped to one."""
    counters = {}
    result = bump_conversion(counters, "user_42")
    assert result == 1
    assert counters["user_42"] == 1


def test_increment_existing_counter():
    """An existing counter should increase by exactly one."""
    counters = {"user_1": 5}
    result = bump_conversion(counters, "user_1")
    assert result == 6
    assert counters["user_1"] == 6


def test_no_cap_allows_unlimited_growth():
    """Without a cap the counter should grow without any ceiling."""
    counters = {"evt": 999}
    result = bump_conversion(counters, "evt")
    assert result == 1000


def test_cap_not_reached_allows_normal_increment():
    """When the count is well below the cap, the bump proceeds normally."""
    counters = {"purchase": 2}
    result = bump_conversion(counters, "purchase", cap=10)
    assert result == 3


def test_counter_reaches_cap_exactly():
    """Bumping up to the cap value should clamp at the cap."""
    counters = {"purchase": 4}
    result = bump_conversion(counters, "purchase", cap=5)
    assert result == 5
    assert counters["purchase"] == 5


def test_counter_already_at_cap_stays_at_cap():
    """When the counter is already at the cap, another bump must not exceed it."""
    counters = {"lead": 10}
    result = bump_conversion(counters, "lead", cap=10)
    assert result == 10
    assert counters["lead"] == 10


def test_repeated_bumps_plateau_at_cap():
    """Repeated bumps should plateau at the cap and never decrease."""
    counters = {"click": 0}
    cap = 3
    results = []
    for _ in range(6):
        results.append(bump_conversion(counters, "click", cap=cap))
    assert results == [1, 2, 3, 3, 3, 3]


def test_cap_of_one_clamps_immediately():
    """A cap of 1 means the very first bump should set the counter to 1 and stay."""
    counters = {}
    r1 = bump_conversion(counters, "once", cap=1)
    r2 = bump_conversion(counters, "once", cap=1)
    assert r1 == 1
    assert r2 == 1


def test_invalid_cap_raises_value_error():
    """A cap below the minimum allowed value must raise ValueError."""
    with pytest.raises(ValueError):
        bump_conversion({}, "x", cap=0)


def test_multiple_keys_independent():
    """Counters for different keys must be tracked independently."""
    counters = {}
    bump_conversion(counters, "a")
    bump_conversion(counters, "b")
    bump_conversion(counters, "a")
    assert counters["a"] == 2
    assert counters["b"] == 1
