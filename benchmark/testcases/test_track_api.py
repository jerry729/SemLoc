import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.track_api import track_api
else:
    from programs.track_api import track_api


def test_first_call_initializes_counter():
    """A brand-new endpoint key should start at 1 after the first tracking call."""
    counts = {}
    result = track_api(counts, "/v1/users")
    assert result == 1
    assert counts["/v1/users"] == 1


def test_increments_existing_counter():
    """Subsequent calls should monotonically increment the counter."""
    counts = {"/v1/orders": 3}
    result = track_api(counts, "/v1/orders")
    assert result == 4
    assert counts["/v1/orders"] == 4


def test_no_ceiling_allows_unlimited_growth():
    """Without max_value the counter should grow without bound."""
    counts = {}
    for i in range(1, 101):
        result = track_api(counts, "/v1/health")
    assert result == 100


def test_separate_keys_are_independent():
    """Counters for different API keys must not interfere with each other."""
    counts = {}
    track_api(counts, "/v1/a")
    track_api(counts, "/v1/a")
    track_api(counts, "/v1/b")
    assert counts["/v1/a"] == 2
    assert counts["/v1/b"] == 1


def test_invalid_max_value_raises():
    """A max_value below the minimum threshold must raise ValueError."""
    counts = {}
    with pytest.raises(ValueError):
        track_api(counts, "/v1/x", max_value=0)


def test_ceiling_clamps_at_max_value():
    """The counter should equal max_value once it reaches the ceiling."""
    counts = {"/v1/data": 4}
    result = track_api(counts, "/v1/data", max_value=5)
    assert result == 5
    assert counts["/v1/data"] == 5


def test_counter_stays_at_ceiling_on_repeated_calls():
    """Once clamped, additional calls should keep the counter at the ceiling."""
    counts = {"/v1/data": 9}
    track_api(counts, "/v1/data", max_value=10)
    result = track_api(counts, "/v1/data", max_value=10)
    assert result == 10
    assert counts["/v1/data"] == 10


def test_ceiling_with_max_value_one():
    """A max_value of 1 means the counter should never exceed 1."""
    counts = {}
    r1 = track_api(counts, "/v1/ping", max_value=1)
    assert r1 == 1
    r2 = track_api(counts, "/v1/ping", max_value=1)
    assert r2 == 1


def test_counter_reaches_exact_ceiling():
    """When incrementing to exactly max_value, the returned value must equal max_value."""
    counts = {"/v1/items": 99}
    result = track_api(counts, "/v1/items", max_value=100)
    assert result == 100


def test_ceiling_stability_after_many_calls():
    """After many calls the counter must remain stable at the ceiling value."""
    counts = {}
    for _ in range(50):
        result = track_api(counts, "/v1/stream", max_value=5)
    assert result == 5
    assert counts["/v1/stream"] == 5
