import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.track_build import track_build
else:
    from programs.track_build import track_build


def test_first_increment_from_empty():
    """A fresh counter dict should yield 1 after the first bump."""
    counters = {}
    result = track_build(counters, "compile")
    assert result == 1
    assert counters["compile"] == 1


def test_multiple_increments_no_cap():
    """Without a cap, successive calls should keep incrementing."""
    counters = {}
    for i in range(1, 6):
        result = track_build(counters, "lint")
        assert result == i


def test_different_keys_are_independent():
    """Metrics with different keys must track independently."""
    counters = {}
    track_build(counters, "build")
    track_build(counters, "build")
    track_build(counters, "test")
    assert counters["build"] == 2
    assert counters["test"] == 1


def test_invalid_empty_key_raises():
    """An empty key string must raise ValueError."""
    with pytest.raises(ValueError):
        track_build({}, "")


def test_cap_clamps_value_at_ceiling():
    """Once the counter reaches the cap it must stay at the cap value."""
    counters = {"deploy": 4}
    result = track_build(counters, "deploy", cap=5)
    assert result == 5
    assert counters["deploy"] == 5


def test_cap_holds_after_repeated_calls():
    """Calling track_build repeatedly past the cap should keep the value at cap."""
    counters = {}
    cap = 3
    results = []
    for _ in range(6):
        results.append(track_build(counters, "package", cap=cap))
    assert results == [1, 2, 3, 3, 3, 3]


def test_counter_equals_cap_stays_at_cap():
    """When the counter is already at cap, a new call should return cap."""
    counters = {"ci": 9}
    result = track_build(counters, "ci", cap=10)
    assert result == 10
    result2 = track_build(counters, "ci", cap=10)
    assert result2 == 10


def test_cap_of_one_always_returns_one():
    """A cap of 1 means the metric must never exceed 1."""
    counters = {}
    r1 = track_build(counters, "release", cap=1)
    assert r1 == 1
    r2 = track_build(counters, "release", cap=1)
    assert r2 == 1
    r3 = track_build(counters, "release", cap=1)
    assert r3 == 1


def test_returned_value_matches_stored_value():
    """The return value must always match what is stored in the counters dict."""
    counters = {}
    for _ in range(5):
        result = track_build(counters, "scan", cap=3)
        assert result == counters["scan"]
