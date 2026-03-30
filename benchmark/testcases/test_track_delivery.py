import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.track_delivery import track_delivery
else:
    from programs.track_delivery import track_delivery


def test_new_key_starts_at_one():
    """A fresh delivery key should have its counter set to 1 after the first attempt."""
    counters = {}
    result = track_delivery(counters, "route_A")
    assert result == 1
    assert counters["route_A"] == 1


def test_increment_existing_key():
    """An existing counter should increase by one on each call."""
    counters = {"route_B": 3}
    result = track_delivery(counters, "route_B")
    assert result == 4
    assert counters["route_B"] == 4


def test_no_cap_unlimited_growth():
    """Without a cap, the counter should grow without any upper bound."""
    counters = {"route_C": 999}
    result = track_delivery(counters, "route_C")
    assert result == 1000


def test_cap_below_minimum_raises():
    """A cap value below the minimum threshold must raise a ValueError."""
    counters = {}
    with pytest.raises(ValueError):
        track_delivery(counters, "route_D", cap=0)


def test_counter_below_cap_increments_normally():
    """When the counter is well below the cap, normal increment should apply."""
    counters = {"route_E": 2}
    result = track_delivery(counters, "route_E", cap=10)
    assert result == 3


def test_counter_reaches_cap_stays_at_cap():
    """When incrementing would reach the cap, the counter should be set to the cap value."""
    counters = {"route_F": 4}
    result = track_delivery(counters, "route_F", cap=5)
    assert result == 5
    assert counters["route_F"] == 5


def test_counter_already_at_cap_stays_at_cap():
    """Repeated calls after reaching the cap should keep the counter at the cap."""
    counters = {"route_G": 5}
    result = track_delivery(counters, "route_G", cap=5)
    assert result == 5
    assert counters["route_G"] == 5


def test_counter_does_not_oscillate_at_cap():
    """Calling track_delivery multiple times at the cap must yield a stable value."""
    counters = {"route_H": 9}
    track_delivery(counters, "route_H", cap=10)
    r1 = track_delivery(counters, "route_H", cap=10)
    r2 = track_delivery(counters, "route_H", cap=10)
    assert r1 == r2 == 10


def test_cap_of_one_clamps_immediately():
    """A cap of 1 means the counter should reach 1 and never exceed it."""
    counters = {}
    r1 = track_delivery(counters, "route_I", cap=1)
    assert r1 == 1
    r2 = track_delivery(counters, "route_I", cap=1)
    assert r2 == 1


def test_multiple_keys_independent():
    """Different keys should have independent counters even with the same cap."""
    counters = {}
    track_delivery(counters, "alpha", cap=3)
    track_delivery(counters, "alpha", cap=3)
    track_delivery(counters, "beta", cap=3)
    assert counters["alpha"] == 2
    assert counters["beta"] == 1
