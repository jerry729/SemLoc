import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.error_meter import error_meter
else:
    from programs.error_meter import error_meter


def test_new_key_initialised_to_one():
    """A previously-unseen metric key should start at 1 after a single bump."""
    counters = {}
    result = error_meter(counters, "http_500")
    assert result == 1
    assert counters["http_500"] == 1


def test_increments_existing_counter():
    """Successive calls must monotonically increment the counter."""
    counters = {"timeout": 3}
    result = error_meter(counters, "timeout")
    assert result == 4


def test_no_cap_allows_unlimited_growth():
    """Without a cap the counter should grow without bound."""
    counters = {}
    for _ in range(100):
        error_meter(counters, "oom")
    assert counters["oom"] == 100


def test_cap_not_reached_returns_actual_count():
    """When the counter is below the cap the raw count is returned."""
    counters = {}
    result = error_meter(counters, "dns_fail", cap=10)
    assert result == 1


def test_counter_reaches_cap_exactly():
    """When the counter hits the cap value it should be clamped to the cap."""
    counters = {"auth_err": 4}
    result = error_meter(counters, "auth_err", cap=5)
    assert result == 5
    assert counters["auth_err"] == 5


def test_counter_stays_at_cap_after_repeated_bumps():
    """Repeated increments past the cap should keep the counter at the cap."""
    counters = {}
    for _ in range(20):
        val = error_meter(counters, "rate_limit", cap=7)
    assert val == 7
    assert counters["rate_limit"] == 7


def test_cap_of_one_clamps_immediately():
    """A cap of 1 means the counter should stay at 1 forever."""
    counters = {}
    error_meter(counters, "fatal", cap=1)
    error_meter(counters, "fatal", cap=1)
    error_meter(counters, "fatal", cap=1)
    assert counters["fatal"] == 1


def test_multiple_keys_independent_caps():
    """Each metric key should maintain its own independent capped counter."""
    counters = {}
    for _ in range(10):
        error_meter(counters, "a", cap=3)
        error_meter(counters, "b", cap=5)
    assert counters["a"] == 3
    assert counters["b"] == 5


def test_invalid_cap_raises_value_error():
    """A cap below the minimum threshold must raise a ValueError."""
    with pytest.raises(ValueError):
        error_meter({}, "bad", cap=0)


def test_counter_value_equals_cap_after_exceeding():
    """Once the counter overshoots the cap it must be pinned to exactly the cap value."""
    counters = {"conn_refused": 9}
    result = error_meter(counters, "conn_refused", cap=10)
    assert result == 10
    result2 = error_meter(counters, "conn_refused", cap=10)
    assert result2 == 10
