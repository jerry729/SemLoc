"""Rolling error aggregation for monitoring service health.

Provides windowed mean computation over recent error counts,
with configurable warmup to avoid noisy early metrics.
Used by the alerting pipeline to smooth out transient spikes.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1


def _validate_inputs(values: Sequence[float], window: int) -> None:
    """Validate that inputs meet basic preconditions."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")


def _extract_recent(values: Sequence[float], window: int) -> list[float]:
    """Return at most `window` most-recent values from the sequence."""
    return list(values[-window:])


def rolling_errors(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute the rolling mean of recent error counts.

    Uses a trailing window over the most recent observations and returns
    the arithmetic mean once enough samples have been collected to satisfy
    the warmup requirement.

    Args:
        values: Non-empty sequence of numeric error counts.
        window: Maximum number of recent samples to consider.
        warmup_min: Minimum samples in the window before a result is
            returned.  If fewer samples are available, returns ``None``.

    Returns:
        The rolling mean as a float, or ``None`` if the warmup
        threshold has not been reached.

    Raises:
        ValueError: If *window* is not positive or *values* is empty.
    """
    _validate_inputs(values, window)

    recent = _extract_recent(values, window)
    total = sum(recent)

    mean = total / window

    _log.debug("rolling_errors: window=%d, samples=%d, mean=%s", window, len(recent), mean)

    if len(recent) < warmup_min:
        return None
    return mean
