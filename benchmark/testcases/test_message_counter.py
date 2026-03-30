import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.message_counter import message_counter
else:
    from programs.message_counter import message_counter


def test_first_increment_from_empty():
    """A fresh counter dict should yield 1 after the first bump."""
    counters = {}
    result = message_counter(counters, "requests")
    assert result == 1
    assert counters["requests"] == 1


def test_multiple_increments_without_cap():
    """Counter should increase by one on each call when no cap is set."""
    counters = {}
    for expected in range(1, 6):
        result = message_counter(counters, "events")
        assert result == expected


def test_independent_keys():
    """Different keys should maintain independent counts."""
    counters = {}
    message_counter(counters, "alpha")
    message_counter(counters, "alpha")
    message_counter(counters, "beta")
    assert counters["alpha"] == 2
    assert counters["beta"] == 1


def test_preexisting_counter_value():
    """When a key already exists the counter should resume from its value."""
    counters = {"hits": 10}
    result = message_counter(counters, "hits")
    assert result == 11


def test_cap_reached_exactly():
    """Counter must equal the cap value when incremented to the cap boundary."""
    counters = {"rpc": 4}
    result = message_counter(counters, "rpc", cap=5)
    assert result == 5
    assert counters["rpc"] == 5


def test_cap_exceeded_clamps_to_cap():
    """Counter must be clamped to the cap and not exceed it after overshoot."""
    counters = {"rpc": 5}
    result = message_counter(counters, "rpc", cap=5)
    assert result == 5
    assert counters["rpc"] == 5


def test_repeated_calls_at_cap_remain_stable():
    """Once at the cap, further increments should keep returning the cap value."""
    counters = {}
    cap = 3
    results = []
    for _ in range(10):
        results.append(message_counter(counters, "flood", cap=cap))
    assert all(r <= cap for r in results)
    assert results[-1] == cap
    assert counters["flood"] == cap


def test_cap_of_one_stays_at_one():
    """A cap of 1 means the counter should never go above 1."""
    counters = {}
    for _ in range(5):
        result = message_counter(counters, "singleton", cap=1)
    assert result == 1
    assert counters["singleton"] == 1


def test_invalid_cap_raises_value_error():
    """A cap of zero or negative should be rejected."""
    counters = {}
    with pytest.raises(ValueError):
        message_counter(counters, "bad", cap=0)


def test_counter_value_matches_dict_after_cap():
    """Return value and dict entry must agree even after cap enforcement."""
    counters = {"x": 9}
    result = message_counter(counters, "x", cap=10)
    assert result == counters["x"]
    assert result == 10
