import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.retry_backoff_window import retry_backoff_window
else:
    from programs.retry_backoff_window import retry_backoff_window


def test_zero_attempts_returns_base_delay():
    """With zero prior attempts the delay should equal the base value."""
    assert retry_backoff_window(0) == 1


def test_first_retry_doubles_base():
    """The first retry should produce twice the base delay."""
    assert retry_backoff_window(1) == 2


def test_exponential_growth_low_attempts():
    """Delay should grow exponentially for small attempt counts."""
    assert retry_backoff_window(3) == 8


def test_negative_attempts_raises():
    """Negative attempt counts are invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        retry_backoff_window(-1)


def test_custom_base_scales_delay():
    """A custom base delay should scale the backoff proportionally."""
    assert retry_backoff_window(2, base=3) == 12


def test_delay_never_exceeds_max():
    """The returned delay must never exceed the configured maximum."""
    result = retry_backoff_window(10, max_delay=60)
    assert result <= 60


def test_delay_equals_max_when_raw_equals_cap():
    """When the raw exponential value exactly equals max_delay, the result should be max_delay."""
    result = retry_backoff_window(6, base=1, max_delay=64)
    assert result == 64


def test_large_attempts_capped_at_max():
    """Very large attempt values must still be capped at max_delay."""
    result = retry_backoff_window(20, max_delay=30)
    assert result == 30


def test_cap_with_custom_base_and_max():
    """Capping should work correctly with non-default base and max_delay."""
    result = retry_backoff_window(5, base=2, max_delay=50)
    assert result == 50


def test_monotonic_up_to_cap():
    """Delays should increase monotonically until the cap, then remain at exactly max_delay."""
    delays = [retry_backoff_window(i, max_delay=32) for i in range(10)]
    for i in range(1, len(delays)):
        assert delays[i] >= delays[i - 1]
    assert all(d <= 32 for d in delays)
