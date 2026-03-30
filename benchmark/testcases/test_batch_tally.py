import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.batch_tally import batch_tally
else:
    from programs.batch_tally import batch_tally


def test_first_tally_creates_entry():
    """A previously unseen key should start at count 1."""
    counts = {}
    result = batch_tally(counts, "job_alpha")
    assert result == 1
    assert counts["job_alpha"] == 1


def test_increments_existing_key():
    """Tallying a key already present should increase it by one."""
    counts = {"task_x": 3}
    result = batch_tally(counts, "task_x")
    assert result == 4
    assert counts["task_x"] == 4


def test_no_max_value_unlimited_growth():
    """Without a ceiling, the counter should grow without bound."""
    counts = {}
    for i in range(1, 51):
        result = batch_tally(counts, "unlimited")
        assert result == i


def test_separate_keys_independent():
    """Different keys should maintain independent tallies."""
    counts = {}
    batch_tally(counts, "alpha")
    batch_tally(counts, "alpha")
    batch_tally(counts, "beta")
    assert counts["alpha"] == 2
    assert counts["beta"] == 1


def test_ceiling_clamps_at_max_value():
    """Counter must not exceed the configured ceiling."""
    counts = {"evt": 4}
    result = batch_tally(counts, "evt", max_value=5)
    assert result == 5
    assert counts["evt"] == 5


def test_ceiling_stays_at_max_on_repeated_calls():
    """Repeated tallies at the ceiling should keep returning max_value."""
    counts = {"evt": 9}
    r1 = batch_tally(counts, "evt", max_value=10)
    r2 = batch_tally(counts, "evt", max_value=10)
    r3 = batch_tally(counts, "evt", max_value=10)
    assert r1 == 10
    assert r2 == 10
    assert r3 == 10
    assert counts["evt"] == 10


def test_counter_reaches_max_exactly():
    """When incrementing to exactly max_value, the result should equal max_value."""
    counts = {}
    max_val = 3
    results = []
    for _ in range(5):
        results.append(batch_tally(counts, "k", max_value=max_val))
    assert results == [1, 2, 3, 3, 3]


def test_ceiling_of_one_always_returns_one():
    """A ceiling of 1 means the counter should saturate at 1 immediately."""
    counts = {}
    r1 = batch_tally(counts, "single", max_value=1)
    r2 = batch_tally(counts, "single", max_value=1)
    assert r1 == 1
    assert r2 == 1


def test_invalid_max_value_raises():
    """A max_value below the minimum allowed threshold should raise ValueError."""
    counts = {}
    with pytest.raises(ValueError):
        batch_tally(counts, "bad", max_value=0)


def test_dict_reflects_clamped_value():
    """The counts dictionary should store the clamped value, not the raw increment."""
    counts = {"x": 7}
    batch_tally(counts, "x", max_value=5)
    assert counts["x"] == 5
