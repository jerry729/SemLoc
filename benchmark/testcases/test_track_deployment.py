import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.track_deployment import track_deployment
else:
    from programs.track_deployment import track_deployment


def test_first_deployment_event_initializes_counter():
    """A new service key should start at count 1 after the first event."""
    counts = {}
    result = track_deployment(counts, "web-api")
    assert result == 1
    assert counts["web-api"] == 1


def test_successive_increments_without_ceiling():
    """Each call without a ceiling should increment the counter by one."""
    counts = {}
    track_deployment(counts, "worker")
    track_deployment(counts, "worker")
    result = track_deployment(counts, "worker")
    assert result == 3


def test_independent_keys_tracked_separately():
    """Different service keys maintain independent counters."""
    counts = {}
    track_deployment(counts, "auth-service")
    track_deployment(counts, "auth-service")
    track_deployment(counts, "billing")
    assert counts["auth-service"] == 2
    assert counts["billing"] == 1


def test_empty_key_raises_value_error():
    """An empty deployment key should be rejected."""
    counts = {}
    with pytest.raises(ValueError):
        track_deployment(counts, "")


def test_counter_below_ceiling_increments_normally():
    """When the counter is well below the ceiling it should increment freely."""
    counts = {}
    result = track_deployment(counts, "gateway", max_value=10)
    assert result == 1


def test_counter_reaches_ceiling_exactly():
    """The counter must equal the ceiling value when it reaches the limit."""
    counts = {"scheduler": 4}
    result = track_deployment(counts, "scheduler", max_value=5)
    assert result == 5
    assert counts["scheduler"] == 5


def test_counter_stays_at_ceiling_on_repeated_calls():
    """Once at the ceiling, further calls should keep the counter at the ceiling."""
    counts = {"db-migrator": 9}
    track_deployment(counts, "db-migrator", max_value=10)
    result = track_deployment(counts, "db-migrator", max_value=10)
    assert result == 10
    assert counts["db-migrator"] == 10


def test_counter_never_exceeds_ceiling():
    """The counter value must never surpass the configured maximum."""
    counts = {"notifier": 99}
    result = track_deployment(counts, "notifier", max_value=100)
    assert result <= 100
    assert result == 100


def test_ceiling_of_one_clamps_immediately():
    """A ceiling of 1 should clamp the counter to 1 on the very first event."""
    counts = {}
    result = track_deployment(counts, "singleton-svc", max_value=1)
    assert result == 1
    result2 = track_deployment(counts, "singleton-svc", max_value=1)
    assert result2 == 1


def test_counter_at_ceiling_does_not_decrease():
    """A counter already at the ceiling must not drop below it on subsequent tracking."""
    counts = {"edge-proxy": 5}
    result = track_deployment(counts, "edge-proxy", max_value=5)
    assert result == 5
    result2 = track_deployment(counts, "edge-proxy", max_value=5)
    assert result2 == 5
