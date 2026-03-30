import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.invoice_meter import invoice_meter
else:
    from programs.invoice_meter import invoice_meter


def test_first_increment_from_empty():
    """A fresh event key should start at zero and increment to one."""
    counts = {}
    result = invoice_meter(counts, "api_call")
    assert result == 1
    assert counts["api_call"] == 1


def test_multiple_increments_without_cap():
    """Repeated metering without a cap should count linearly."""
    counts = {}
    for i in range(1, 6):
        result = invoice_meter(counts, "download")
        assert result == i


def test_no_cap_unlimited_growth():
    """Without max_value the counter should grow unbounded."""
    counts = {"upload": 9999}
    result = invoice_meter(counts, "upload")
    assert result == 10000


def test_separate_keys_independent():
    """Counters for different event types must be independent."""
    counts = {}
    invoice_meter(counts, "email")
    invoice_meter(counts, "email")
    invoice_meter(counts, "sms")
    assert counts["email"] == 2
    assert counts["sms"] == 1


def test_cap_reached_exactly():
    """When the counter reaches the ceiling it should stay at max_value."""
    counts = {"prints": 4}
    result = invoice_meter(counts, "prints", max_value=5)
    assert result == 5
    assert counts["prints"] == 5


def test_cap_sustained_after_multiple_calls():
    """Repeated increments past the ceiling should keep the counter at max_value."""
    counts = {"prints": 4}
    invoice_meter(counts, "prints", max_value=5)
    result = invoice_meter(counts, "prints", max_value=5)
    assert result == 5
    assert counts["prints"] == 5


def test_cap_of_one_stays_at_one():
    """With a ceiling of 1 the counter should reach 1 and remain there."""
    counts = {}
    r1 = invoice_meter(counts, "singleton", max_value=1)
    assert r1 == 1
    r2 = invoice_meter(counts, "singleton", max_value=1)
    assert r2 == 1


def test_counter_never_exceeds_cap():
    """Over many increments, the counter must never surpass the configured ceiling."""
    counts = {}
    cap = 3
    for _ in range(10):
        result = invoice_meter(counts, "bounded", max_value=cap)
        assert result <= cap
    assert counts["bounded"] == cap


def test_invalid_key_raises():
    """An empty key string should be rejected with a ValueError."""
    counts = {}
    with pytest.raises(ValueError):
        invoice_meter(counts, "")


def test_cap_idempotent_at_ceiling():
    """Calling meter when already at ceiling should return the ceiling value."""
    counts = {"quota": 10}
    result = invoice_meter(counts, "quota", max_value=10)
    assert result == 10
