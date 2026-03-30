import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.track_logout import track_logout
else:
    from programs.track_logout import track_logout


def test_first_logout_increments_from_zero():
    """A fresh user key should go from absent to count 1 on first logout."""
    counters = {}
    result = track_logout(counters, "user_42")
    assert result == 1
    assert counters["user_42"] == 1


def test_multiple_logouts_without_cap():
    """Without a cap, the counter should increment freely across multiple calls."""
    counters = {}
    for i in range(1, 6):
        result = track_logout(counters, "session_abc")
        assert result == i


def test_existing_counter_increments():
    """A pre-existing counter value should be incremented by exactly one."""
    counters = {"user_7": 10}
    result = track_logout(counters, "user_7")
    assert result == 11
    assert counters["user_7"] == 11


def test_cap_below_minimum_raises_error():
    """A cap value below the minimum threshold should raise ValueError."""
    counters = {}
    with pytest.raises(ValueError):
        track_logout(counters, "user_1", cap=0)


def test_counter_does_not_exceed_cap():
    """When a cap is set, the counter must never surpass that cap value."""
    counters = {"user_x": 4}
    result = track_logout(counters, "user_x", cap=5)
    assert result == 5
    assert counters["user_x"] == 5


def test_counter_stays_at_cap_on_repeated_logouts():
    """Repeated logouts beyond the cap should keep the counter pinned at the cap."""
    counters = {"user_x": 5}
    result = track_logout(counters, "user_x", cap=5)
    assert result == 5
    assert counters["user_x"] == 5


def test_counter_reaches_cap_exactly():
    """Incrementing to exactly the cap value should set the counter to the cap."""
    counters = {"usr": 2}
    result = track_logout(counters, "usr", cap=3)
    assert result == 3
    assert counters["usr"] == 3


def test_cap_stability_over_many_iterations():
    """After hitting the cap, the counter must remain stable across 100 additional calls."""
    counters = {}
    cap = 3
    for _ in range(100):
        track_logout(counters, "flood_user", cap=cap)
    assert counters["flood_user"] == cap


def test_independent_keys_tracked_separately():
    """Distinct keys should maintain independent counters."""
    counters = {}
    track_logout(counters, "alice")
    track_logout(counters, "alice")
    track_logout(counters, "bob")
    assert counters["alice"] == 2
    assert counters["bob"] == 1


def test_cap_one_pins_counter_at_one():
    """A cap of 1 should pin the counter at 1 from the first logout onward."""
    counters = {}
    for _ in range(5):
        result = track_logout(counters, "singleton", cap=1)
    assert result == 1
    assert counters["singleton"] == 1
