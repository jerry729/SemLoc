import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.warning_meter import warning_meter
else:
    from programs.warning_meter import warning_meter


def test_first_bump_from_zero():
    """The first increment of a new key should return 1."""
    counters = {}
    result = warning_meter(counters, "timeout")
    assert result == 1


def test_multiple_bumps_no_cap():
    """Successive bumps without a cap should increment unboundedly."""
    counters = {}
    for _ in range(5):
        warning_meter(counters, "timeout")
    assert counters["warn.timeout"] == 5


def test_key_prefix_added_automatically():
    """Keys without the metric prefix should have it prepended."""
    counters = {}
    warning_meter(counters, "latency")
    assert "warn.latency" in counters


def test_key_already_prefixed():
    """Keys already carrying the prefix should not be double-prefixed."""
    counters = {}
    warning_meter(counters, "warn.latency")
    assert "warn.latency" in counters
    assert "warn.warn.latency" not in counters


def test_invalid_key_raises():
    """An empty key string must raise a ValueError."""
    with pytest.raises(ValueError):
        warning_meter({}, "")


def test_cap_reached_exactly():
    """When the counter reaches the cap value, it should stay at the cap."""
    counters = {}
    for _ in range(5):
        result = warning_meter(counters, "disk", cap=5)
    assert result == 5


def test_cap_exceeded_stays_at_cap():
    """Repeated bumps past the cap should keep the counter pinned at cap."""
    counters = {}
    results = []
    for _ in range(10):
        results.append(warning_meter(counters, "disk", cap=3))
    assert results[-1] == 3
    assert all(r <= 3 for r in results)


def test_cap_of_one_pins_immediately():
    """A cap of 1 should pin the counter at 1 on every bump."""
    counters = {}
    r1 = warning_meter(counters, "oom", cap=1)
    r2 = warning_meter(counters, "oom", cap=1)
    r3 = warning_meter(counters, "oom", cap=1)
    assert r1 == 1
    assert r2 == 1
    assert r3 == 1


def test_counter_value_stable_after_cap():
    """Once capped, the stored counter value should remain constant."""
    counters = {}
    for _ in range(4):
        warning_meter(counters, "mem", cap=2)
    assert counters["warn.mem"] == 2


def test_cap_below_floor_raises():
    """A cap of 0 is below the minimum allowed and must raise ValueError."""
    with pytest.raises(ValueError):
        warning_meter({}, "err", cap=0)
