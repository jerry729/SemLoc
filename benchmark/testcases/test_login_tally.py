import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.login_tally import login_tally
else:
    from programs.login_tally import login_tally


def test_first_login_attempt_starts_at_one():
    """A fresh user should have their counter set to 1 after the first attempt."""
    counters = {}
    result = login_tally(counters, "user_alice")
    assert result == 1
    assert counters["user_alice"] == 1


def test_increments_existing_counter():
    """Subsequent login attempts should increment the counter by one."""
    counters = {"user_bob": 3}
    result = login_tally(counters, "user_bob")
    assert result == 4
    assert counters["user_bob"] == 4


def test_no_cap_allows_unlimited_growth():
    """Without a cap, the counter should grow without any upper bound."""
    counters = {"user_carol": 999}
    result = login_tally(counters, "user_carol")
    assert result == 1000


def test_counter_below_cap_increments_normally():
    """When the counter is well below the cap, it should increment by one."""
    counters = {"user_dave": 2}
    result = login_tally(counters, "user_dave", cap=10)
    assert result == 3
    assert counters["user_dave"] == 3


def test_invalid_cap_raises_value_error():
    """A cap value of zero should be rejected as invalid."""
    counters = {}
    with pytest.raises(ValueError):
        login_tally(counters, "user_eve", cap=0)


def test_counter_reaches_cap_exactly():
    """When incrementing would reach the cap, the result should equal the cap."""
    counters = {"user_frank": 4}
    result = login_tally(counters, "user_frank", cap=5)
    assert result == 5
    assert counters["user_frank"] == 5


def test_counter_already_at_cap_stays_at_cap():
    """Once the counter is at the cap, further increments should stay at the cap."""
    counters = {"user_grace": 5}
    result = login_tally(counters, "user_grace", cap=5)
    assert result == 5
    assert counters["user_grace"] == 5


def test_counter_exceeds_cap_clamps_to_cap():
    """If the counter would exceed the cap, it should be clamped to the cap value."""
    counters = {"user_heidi": 10}
    result = login_tally(counters, "user_heidi", cap=5)
    assert result == 5
    assert counters["user_heidi"] == 5


def test_repeated_calls_at_cap_remain_stable():
    """Repeated increments at the cap should produce a stable counter value."""
    counters = {"user_ivan": 3}
    for _ in range(10):
        result = login_tally(counters, "user_ivan", cap=5)
    assert result == 5
    assert counters["user_ivan"] == 5


def test_cap_of_one_clamps_immediately():
    """A cap of 1 should clamp the counter to 1 on the very first attempt."""
    counters = {}
    result = login_tally(counters, "user_judy", cap=1)
    assert result == 1
    assert counters["user_judy"] == 1
