"""Rolling retry-rate smoother for distributed service health monitoring.

Provides a windowed rolling mean of retry counts observed across
service replicas, used by the alerting pipeline to suppress
transient spikes and only fire alerts on sustained retry pressure.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1      # minimum observations before emitting a metric
_DEFAULT_WINDOW = 3       # default sliding-window width
_MAX_WINDOW = 1024        # guard against absurdly large windows


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed size of {_MAX_WINDOW}")


def _extract_tail(values: Sequence[float], window: int) -> Sequence[float]:
    """Return the last *window* elements of *values*."""
    return values[-window:]


def rolling_retries(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute the rolling mean of retry counts over a sliding window.

    Args:
        values: Non-empty sequence of per-interval retry counts.
        window: Width of the sliding window (positive integer).
        warmup_min: Minimum number of samples in the tail before a
            result is emitted.  If the tail is shorter, ``None`` is
            returned to signal insufficient data.

    Returns:
        The rolling mean as a float, or ``None`` when the warmup
        threshold has not been met.

    Raises:
        ValueError: If *window* is non-positive, exceeds ``_MAX_WINDOW``,
            or *values* is empty.
    """
    _validate_window(window)
    if not values:
        raise ValueError("empty series")

    tail = _extract_tail(values, window)
    total = sum(tail)

    mean = total / window

    _log.debug("tail=%s total=%.4f mean=%.4f", tail, total, mean)

    if len(tail) < warmup_min:
        return None
    return mean
