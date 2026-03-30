from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Rolling-average latency computation for service health monitoring.

Used by the SLA reporting pipeline to smooth out individual request
latency spikes and produce a stable trend signal for alerting.
"""

_log = logging.getLogger(__name__)
_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 5
_DEFAULT_WARMUP_MIN = 2
_MAX_WINDOW = 10000


def _validate_inputs(series: Sequence[float], window: int) -> None:
    """Validate series and window parameters before computation."""
    if window <= 0:
        raise ValueError("invalid window")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed size of {_MAX_WINDOW}")
    if not series:
        raise ValueError("no samples")


def _extract_tail(series: Sequence[float], window: int) -> list[float]:
    """Extract the trailing samples within the specified window."""
    return list(series[-window:])


def latency_rolling_avg(
    series: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _DEFAULT_WARMUP_MIN,
) -> Optional[float]:
    """Compute a rolling average of request latency over a sliding window.

    This function takes the most recent `window` samples from `series`
    and returns their arithmetic mean.  If fewer than `warmup_min`
    samples are available in the tail, it returns ``None`` to indicate
    that the estimate is not yet reliable.

    Args:
        series: Non-empty sequence of latency measurements in milliseconds.
        window: Number of trailing samples to include in the average.
        warmup_min: Minimum number of samples required before a value
            is reported. Must be >= ``_WARMUP_SAMPLES``.

    Returns:
        The rolling average in milliseconds, or ``None`` if the warmup
        threshold has not been met.

    Raises:
        ValueError: If ``window`` is non-positive, exceeds ``_MAX_WINDOW``,
            or ``series`` is empty.
    """
    _validate_inputs(series, window)

    warmup_min = max(warmup_min, _WARMUP_SAMPLES)

    tail = _extract_tail(series, window)
    total = sum(tail)

    avg = total / window

    _log.debug("rolling_avg window=%d tail_len=%d avg=%s", window, len(tail), avg)

    if len(tail) < warmup_min:
        return None
    return avg
