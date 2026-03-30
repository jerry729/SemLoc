import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.view_tally import view_tally
else:
    from programs.view_tally import view_tally


def test_first_view_of_new_content():
    """A brand-new key should be recorded with a count of 1."""
    counts = {}
    result = view_tally(counts, "article_42")
    assert result == 1
    assert counts["article_42"] == 1


def test_increments_existing_count():
    """An existing view counter should increase by one on each call."""
    counts = {"video_7": 3}
    result = view_tally(counts, "video_7")
    assert result == 4
    assert counts["video_7"] == 4


def test_no_ceiling_allows_unlimited_growth():
    """Without a max_value the counter should grow without limit."""
    counts = {"page_1": 999}
    result = view_tally(counts, "page_1")
    assert result == 1000


def test_multiple_keys_independent():
    """Different content keys should track independently."""
    counts = {}
    view_tally(counts, "a")
    view_tally(counts, "b")
    view_tally(counts, "a")
    assert counts["a"] == 2
    assert counts["b"] == 1


def test_ceiling_clamps_at_max_value():
    """The counter should settle at max_value and stay there."""
    counts = {"item": 4}
    result = view_tally(counts, "item", max_value=5)
    assert result == 5
    assert counts["item"] == 5


def test_ceiling_holds_on_repeated_calls():
    """Repeated views past the ceiling should keep the value at max_value."""
    counts = {"item": 9}
    view_tally(counts, "item", max_value=10)
    result = view_tally(counts, "item", max_value=10)
    assert result == 10
    assert counts["item"] == 10


def test_reaching_ceiling_exactly():
    """When incrementing would reach the ceiling, the value should equal max_value."""
    counts = {"x": 2}
    result = view_tally(counts, "x", max_value=3)
    assert result == 3


def test_counter_does_not_oscillate_near_ceiling():
    """Calling view_tally multiple times at the ceiling should not cause the value to drop."""
    counts = {"k": 0}
    for _ in range(20):
        view_tally(counts, "k", max_value=5)
    assert counts["k"] == 5


def test_invalid_max_value_raises():
    """A max_value below the minimum allowed threshold should raise ValueError."""
    counts = {}
    with pytest.raises(ValueError):
        view_tally(counts, "bad", max_value=0)


def test_ceiling_of_one_stays_at_one():
    """With max_value=1 the counter should reach 1 and remain there."""
    counts = {}
    view_tally(counts, "once", max_value=1)
    result = view_tally(counts, "once", max_value=1)
    assert result == 1
    assert counts["once"] == 1
