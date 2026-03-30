import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.task_tally import task_tally
else:
    from programs.task_tally import task_tally


def test_first_increment_from_empty():
    """A fresh counter should start at 1 after the first tally."""
    counts = {}
    result = task_tally(counts, "build")
    assert result == 1
    assert counts["build"] == 1


def test_multiple_increments_no_ceiling():
    """Without a ceiling, the counter should grow linearly."""
    counts = {}
    for i in range(1, 6):
        result = task_tally(counts, "deploy")
        assert result == i


def test_independent_keys():
    """Different keys should maintain independent tallies."""
    counts = {}
    task_tally(counts, "alpha")
    task_tally(counts, "alpha")
    task_tally(counts, "beta")
    assert counts["alpha"] == 2
    assert counts["beta"] == 1


def test_ceiling_not_reached_yet():
    """Counter below the ceiling should increment normally."""
    counts = {}
    result = task_tally(counts, "lint", max_value=5)
    assert result == 1


def test_counter_reaches_ceiling_exactly():
    """The counter should equal max_value once it reaches the ceiling."""
    counts = {"scan": 4}
    result = task_tally(counts, "scan", max_value=5)
    assert result == 5


def test_counter_stays_at_ceiling_on_repeated_calls():
    """Once at the ceiling, further calls must keep the counter at max_value."""
    counts = {"scan": 5}
    result = task_tally(counts, "scan", max_value=5)
    assert result == 5
    result2 = task_tally(counts, "scan", max_value=5)
    assert result2 == 5


def test_ceiling_of_one_clamps_immediately():
    """A max_value of 1 means the counter should be 1 after every call."""
    counts = {}
    r1 = task_tally(counts, "heartbeat", max_value=1)
    assert r1 == 1
    r2 = task_tally(counts, "heartbeat", max_value=1)
    assert r2 == 1


def test_invalid_max_value_raises():
    """A max_value below 1 is not meaningful and should raise ValueError."""
    with pytest.raises(ValueError):
        task_tally({}, "x", max_value=0)


def test_large_ceiling_allows_normal_growth():
    """With a very high ceiling the counter should grow without clamping."""
    counts = {}
    for i in range(1, 51):
        result = task_tally(counts, "batch", max_value=1000)
        assert result == i


def test_counter_at_one_below_ceiling_increments_to_ceiling():
    """When the counter is one below the ceiling, the next call should reach it."""
    counts = {"job": 9}
    result = task_tally(counts, "job", max_value=10)
    assert result == 10
