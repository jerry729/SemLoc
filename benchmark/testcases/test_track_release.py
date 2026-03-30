import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.track_release import track_release
else:
    from programs.track_release import track_release


def test_first_release_initializes_counter():
    """A brand-new artifact key should start at zero and be incremented to one."""
    counters = {}
    result = track_release(counters, "service-api")
    assert result == 1
    assert counters["service-api"] == 1


def test_successive_increments_without_cap():
    """Counters without a cap should grow monotonically with each release."""
    counters = {"backend": 5}
    result = track_release(counters, "backend")
    assert result == 6
    result = track_release(counters, "backend")
    assert result == 7


def test_cap_not_reached_allows_normal_increment():
    """When the counter is well below the cap, increment proceeds normally."""
    counters = {"frontend": 2}
    result = track_release(counters, "frontend", cap=10)
    assert result == 3


def test_invalid_empty_key_raises():
    """An empty string key should be rejected to prevent silent data corruption."""
    counters = {}
    with pytest.raises(ValueError):
        track_release(counters, "")


def test_invalid_non_string_key_raises():
    """Non-string keys should be rejected with a clear error."""
    counters = {}
    with pytest.raises(ValueError):
        track_release(counters, 42)


def test_counter_reaches_cap_exactly():
    """When the next increment would equal the cap, the counter should be set to the cap value."""
    counters = {"worker": 9}
    result = track_release(counters, "worker", cap=10)
    assert result == 10
    assert counters["worker"] == 10


def test_counter_already_at_cap_stays_at_cap():
    """Repeated releases at the cap should hold the counter steady at the cap."""
    counters = {"worker": 10}
    result = track_release(counters, "worker", cap=10)
    assert result == 10
    assert counters["worker"] == 10


def test_counter_exceeds_cap_is_clamped_to_cap():
    """If the counter would exceed the cap after increment, it must be clamped to cap."""
    counters = {"batch-job": 14}
    result = track_release(counters, "batch-job", cap=15)
    assert result == 15
    assert counters["batch-job"] == 15


def test_cap_of_one_with_fresh_counter():
    """A cap of 1 should allow exactly one tracked release from a fresh start."""
    counters = {}
    result = track_release(counters, "singleton", cap=1)
    assert result == 1
    assert counters["singleton"] == 1


def test_repeated_releases_at_cap_one_remain_stable():
    """Repeated releases against a cap of 1 should keep the counter at 1."""
    counters = {"singleton": 1}
    result = track_release(counters, "singleton", cap=1)
    assert result == 1
    assert counters["singleton"] == 1
