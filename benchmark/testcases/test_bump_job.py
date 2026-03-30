import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bump_job import bump_job
else:
    from programs.bump_job import bump_job


def test_initial_bump_creates_entry():
    """A new key should be initialised and incremented to 1 on its first bump."""
    counters = {}
    result = bump_job(counters, "build")
    assert result == 1
    assert counters["build"] == 1


def test_successive_bumps_without_cap():
    """Without a cap the counter should grow linearly with each call."""
    counters = {}
    for i in range(1, 6):
        assert bump_job(counters, "deploy") == i


def test_multiple_keys_independent():
    """Counters for different keys must be tracked independently."""
    counters = {}
    bump_job(counters, "alpha")
    bump_job(counters, "alpha")
    bump_job(counters, "beta")
    assert counters["alpha"] == 2
    assert counters["beta"] == 1


def test_cap_not_reached_allows_normal_increment():
    """When the counter is still well below the cap, it should increment normally."""
    counters = {}
    result = bump_job(counters, "scan", cap=10)
    assert result == 1


def test_counter_saturates_at_cap():
    """Once a job reaches its cap it should stay at exactly the cap value."""
    counters = {"lint": 4}
    result = bump_job(counters, "lint", cap=5)
    assert result == 5
    assert counters["lint"] == 5


def test_repeated_bumps_at_cap_stay_at_cap():
    """Repeated bumps after the cap is reached must all return the cap."""
    counters = {}
    cap = 3
    for _ in range(10):
        result = bump_job(counters, "test", cap=cap)
    assert result == cap
    assert counters["test"] == cap


def test_cap_of_one_clamps_immediately():
    """A cap of 1 means the counter should reach 1 and never exceed it."""
    counters = {}
    assert bump_job(counters, "once", cap=1) == 1
    assert bump_job(counters, "once", cap=1) == 1
    assert counters["once"] == 1


def test_cap_equal_to_current_value_stays_stable():
    """When the counter equals the cap, a bump should still return the cap."""
    counters = {"retry": 5}
    result = bump_job(counters, "retry", cap=5)
    assert result == 5


def test_invalid_cap_raises_value_error():
    """A cap of zero or negative must be rejected with a ValueError."""
    with pytest.raises(ValueError):
        bump_job({}, "bad", cap=0)


def test_counter_never_exceeds_cap_after_many_bumps():
    """After many increments the stored counter must not drift above the cap."""
    counters = {}
    cap = 4
    results = [bump_job(counters, "job_x", cap=cap) for _ in range(20)]
    assert all(r <= cap for r in results)
    assert counters["job_x"] == cap
