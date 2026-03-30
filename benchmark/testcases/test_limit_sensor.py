import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.limit_sensor import limit_sensor
else:
    from programs.limit_sensor import limit_sensor


def test_no_prior_actions_allows_sensor():
    """A sensor with no history should be fully allowed with all slots remaining."""
    allowed, remaining = limit_sensor([], now=100.0)
    assert allowed is True
    assert remaining == 5


def test_actions_outside_window_are_ignored():
    """Timestamps older than the sliding window should not count toward the limit."""
    old_timestamps = [10.0, 20.0, 30.0, 40.0, 50.0]
    allowed, remaining = limit_sensor(old_timestamps, now=100.0)
    assert allowed is True
    assert remaining == 5


def test_few_actions_within_window():
    """Two actions inside the window should leave three remaining slots."""
    timestamps = [95.0, 97.0]
    allowed, remaining = limit_sensor(timestamps, now=100.0)
    assert allowed is True
    assert remaining == 3


def test_actions_at_cutoff_boundary_are_included():
    """A timestamp exactly at the cutoff edge should count as active."""
    timestamps = [90.0, 95.0]
    allowed, remaining = limit_sensor(timestamps, now=100.0)
    assert allowed is True
    assert remaining == 3


def test_sensor_denied_when_over_limit():
    """Six actions inside the window should deny the sensor."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
    allowed, remaining = limit_sensor(timestamps, now=100.0, limit=5)
    assert allowed is False
    assert remaining == 0


def test_sensor_denied_at_exact_limit():
    """When exactly the limit number of actions are in the window, the sensor must be denied."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = limit_sensor(timestamps, now=100.0, limit=5)
    assert allowed is False
    assert remaining == 0


def test_remaining_zero_when_at_capacity():
    """At capacity the remaining count should be zero and the sensor must be blocked."""
    timestamps = [96.0, 97.0, 98.0]
    allowed, remaining = limit_sensor(timestamps, now=100.0, limit=3)
    assert allowed is False
    assert remaining == 0


def test_custom_window_and_limit():
    """Custom window and limit values should be respected correctly."""
    timestamps = [198.0, 199.0]
    allowed, remaining = limit_sensor(timestamps, now=200.0, window=5, limit=2)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """Windows outside the supported range must raise ValueError."""
    with pytest.raises(ValueError):
        limit_sensor([], now=100.0, window=0)


def test_single_action_at_limit_boundary():
    """With limit=1 and one action in window, the sensor should be denied."""
    timestamps = [99.0]
    allowed, remaining = limit_sensor(timestamps, now=100.0, limit=1)
    assert allowed is False
    assert remaining == 0
