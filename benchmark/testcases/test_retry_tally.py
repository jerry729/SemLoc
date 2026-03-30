import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.retry_tally import retry_tally
else:
    from programs.retry_tally import retry_tally


def test_first_increment_from_zero():
    """A fresh counter should be 1 after a single bump."""
    counters = {}
    result = retry_tally(counters, "auth")
    assert result == 1
    assert counters["auth"] == 1


def test_successive_increments_without_cap():
    """Without a cap, repeated calls should yield monotonically increasing values."""
    counters = {}
    for expected in range(1, 6):
        result = retry_tally(counters, "fetch")
        assert result == expected


def test_existing_counter_continues():
    """When a counter already exists it should increment from its current value."""
    counters = {"dns": 5}
    result = retry_tally(counters, "dns")
    assert result == 6


def test_independent_keys():
    """Different keys must be tracked independently."""
    counters = {}
    retry_tally(counters, "alpha")
    retry_tally(counters, "alpha")
    retry_tally(counters, "beta")
    assert counters["alpha"] == 2
    assert counters["beta"] == 1


def test_cap_not_reached_allows_normal_increment():
    """When the counter is well below the cap, incrementing should proceed normally."""
    counters = {}
    result = retry_tally(counters, "conn", cap=10)
    assert result == 1


def test_counter_reaches_cap_exactly():
    """A counter that reaches the cap value should be clamped to the cap."""
    counters = {"rpc": 4}
    result = retry_tally(counters, "rpc", cap=5)
    assert result == 5
    assert counters["rpc"] == 5


def test_counter_stays_at_cap_on_repeated_calls():
    """Once at the cap, further increments must not push the counter above it."""
    counters = {"rpc": 5}
    result = retry_tally(counters, "rpc", cap=5)
    assert result == 5
    assert counters["rpc"] == 5


def test_cap_prevents_exceeding_maximum():
    """Repeated retries beyond the cap must always return the cap value."""
    counters = {}
    for _ in range(20):
        result = retry_tally(counters, "timeout", cap=3)
    assert result == 3
    assert counters["timeout"] == 3


def test_cap_equals_one_clamps_immediately():
    """A cap of 1 should clamp the very first increment to 1."""
    counters = {}
    result = retry_tally(counters, "single", cap=1)
    assert result == 1
    assert counters["single"] == 1


def test_invalid_cap_raises_value_error():
    """A cap below the minimum floor must raise a ValueError."""
    with pytest.raises(ValueError):
        retry_tally({}, "bad", cap=0)
