import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bump_click import bump_click
else:
    from programs.bump_click import bump_click


def test_basic_increment_from_zero():
    """A fresh counter should be 1 after a single bump."""
    counters = {}
    result = bump_click(counters, "page_view")
    assert result == 1
    assert counters["page_view"] == 1


def test_successive_increments_without_cap():
    """Without a cap, consecutive bumps should increase the count linearly."""
    counters = {}
    for i in range(5):
        result = bump_click(counters, "ad_click")
    assert result == 5
    assert counters["ad_click"] == 5


def test_multiple_keys_are_independent():
    """Each metric key maintains its own independent counter."""
    counters = {}
    bump_click(counters, "banner")
    bump_click(counters, "banner")
    bump_click(counters, "sidebar")
    assert counters["banner"] == 2
    assert counters["sidebar"] == 1


def test_cap_not_reached_allows_normal_increment():
    """When the count is well below the cap, the bump proceeds normally."""
    counters = {}
    result = bump_click(counters, "cta", cap=10)
    assert result == 1


def test_counter_reaches_cap_value():
    """A counter bumped exactly to the cap should equal the cap."""
    counters = {"impressions": 4}
    result = bump_click(counters, "impressions", cap=5)
    assert result == 5
    assert counters["impressions"] == 5


def test_counter_stays_at_cap_after_exceeding():
    """Once a counter hits the cap, further bumps should keep it at the cap."""
    counters = {"clicks": 9}
    result = bump_click(counters, "clicks", cap=10)
    assert result == 10
    result2 = bump_click(counters, "clicks", cap=10)
    assert result2 == 10
    assert counters["clicks"] == 10


def test_counter_clamped_at_cap_repeatedly():
    """Bumping many times past the cap must not let the counter oscillate."""
    counters = {}
    cap = 3
    results = []
    for _ in range(6):
        results.append(bump_click(counters, "rate_limited", cap=cap))
    assert results == [1, 2, 3, 3, 3, 3]


def test_cap_of_one_limits_to_single_click():
    """A cap of 1 should allow only one click registration."""
    counters = {}
    r1 = bump_click(counters, "single", cap=1)
    r2 = bump_click(counters, "single", cap=1)
    assert r1 == 1
    assert r2 == 1


def test_invalid_empty_key_raises():
    """An empty key string should be rejected with a ValueError."""
    counters = {}
    with pytest.raises(ValueError):
        bump_click(counters, "")


def test_cap_below_minimum_raises():
    """A cap of zero violates the minimum cap constraint."""
    counters = {}
    with pytest.raises(ValueError):
        bump_click(counters, "test_metric", cap=0)
