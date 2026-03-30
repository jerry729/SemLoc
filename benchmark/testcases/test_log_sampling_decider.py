import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.log_sampling_decider import log_sampling_decider
else:
    from programs.log_sampling_decider import log_sampling_decider


def test_rate_of_zero_never_samples():
    """A sampling rate of 0 should reject every log line unconditionally."""
    ids = [f"event-{i}" for i in range(200)]
    results = [log_sampling_decider(lid, rate=0) for lid in ids]
    assert all(r is False for r in results)


def test_rate_of_one_always_samples():
    """A sampling rate of 1 should accept every log line unconditionally."""
    ids = [f"trace-{i}" for i in range(200)]
    results = [log_sampling_decider(lid, rate=1) for lid in ids]
    assert all(r is True for r in results)


def test_invalid_rate_raises_value_error():
    """Rates outside the [0,1] interval must be rejected immediately."""
    with pytest.raises(ValueError):
        log_sampling_decider("abc", rate=1.5)
    with pytest.raises(ValueError):
        log_sampling_decider("abc", rate=-0.01)


def test_deterministic_for_same_id():
    """Repeated calls with the same log_id and rate must return the same decision."""
    for _ in range(50):
        assert log_sampling_decider("stable-key", rate=0.5) == log_sampling_decider("stable-key", rate=0.5)


def test_returns_boolean_type():
    """The return value must always be a bool."""
    result = log_sampling_decider(42, rate=0.5)
    assert isinstance(result, bool)


def test_approximate_sample_proportion():
    """With a 50%% rate over many distinct ids, roughly half should be sampled."""
    ids = list(range(10000))
    sampled = sum(1 for lid in ids if log_sampling_decider(lid, rate=0.5))
    proportion = sampled / len(ids)
    assert 0.35 < proportion < 0.65


def test_low_rate_samples_fewer_than_high_rate():
    """Increasing the rate must sample at least as many log lines."""
    ids = list(range(5000))
    count_low = sum(1 for lid in ids if log_sampling_decider(lid, rate=0.1))
    count_high = sum(1 for lid in ids if log_sampling_decider(lid, rate=0.9))
    assert count_high >= count_low


def test_sampled_at_low_rate_also_sampled_at_high_rate():
    """Any id sampled at a lower rate must also be sampled at every higher rate."""
    ids = list(range(3000))
    for lid in ids:
        if log_sampling_decider(lid, rate=0.2):
            assert log_sampling_decider(lid, rate=0.8)


def test_ten_percent_rate_rough_proportion():
    """At a 10%% sample rate the proportion of sampled ids should be near 0.1."""
    ids = [f"req-{i}" for i in range(10000)]
    sampled = sum(1 for lid in ids if log_sampling_decider(lid, rate=0.1))
    proportion = sampled / len(ids)
    assert 0.05 < proportion < 0.20


def test_default_rate_is_ten_percent():
    """When no rate is specified the default 10%% rate should apply."""
    ids = list(range(10000))
    sampled = sum(1 for lid in ids if log_sampling_decider(lid))
    proportion = sampled / len(ids)
    assert 0.03 < proportion < 0.25
