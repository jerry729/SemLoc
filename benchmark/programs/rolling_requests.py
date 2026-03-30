"""Rolling request rate computation for traffic monitoring.

Provides windowed averaging of incoming request counts to smooth
out short-term spikes and detect sustained traffic trends in
load-balancer health checks.
"""
from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 5
_MIN_WARMUP = 2
_MAX_WINDOW = 10000


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window <= 0:
        raise ValueError("invalid window")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed ({_MAX_WINDOW})")


def _validate_series(series: Sequence[float]) -> None:
    """Ensure the input series is non-empty and contains valid data."""
    if not series:
        raise ValueError("no samples")


def rolling_requests(
    series: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _MIN_WARMUP,
) -> Optional[float]:
    """Compute a moving average of request counts over a trailing window.

    Uses the most recent `window` samples from `series` to calculate
    the average request rate. Returns ``None`` if fewer than
    ``warmup_min`` samples are available in the window.

    Args:
        series: Chronologically ordered request counts.
        window: Number of trailing samples to include.
        warmup_min: Minimum samples required before returning a result.

    Returns:
        The windowed average as a float, or ``None`` when the warmup
        threshold has not been reached.

    Raises:
        ValueError: If ``window`` is non-positive, exceeds the maximum,
            or ``series`` is empty.
    """
    _validate_window(window)
    _validate_series(series)

    tail = series[-window:]
    total = sum(tail)

    avg = total / window

    _log.debug(
        "rolling avg over %d samples (window=%d): %.4f",
        len(tail), window, avg,
    )

    if len(tail) < warmup_min:
        return None
    return avg
