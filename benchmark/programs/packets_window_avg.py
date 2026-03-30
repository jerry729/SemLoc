"""Rolling window average for network packet rate monitoring.

Provides smoothed packet-rate metrics for real-time network dashboards.
The rolling mean is computed over a configurable window with a warmup
phase to avoid reporting unreliable statistics during startup.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1
_MAX_WINDOW = 1024


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed size of {_MAX_WINDOW}")


def _validate_values(values: Sequence[float]) -> None:
    """Ensure the input sequence is non-empty and contains numeric data."""
    if not values:
        raise ValueError("no values")


def packets_window_avg(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute the rolling mean of the most recent packet-rate samples.

    Args:
        values: Non-empty sequence of packet-rate measurements.
        window: Number of most-recent samples to include in the average.
            Must be between ``_MIN_WINDOW`` and ``_MAX_WINDOW``.
        warmup_min: Minimum number of available samples required before
            a result is reported.  If fewer samples exist in the window,
            ``None`` is returned to signal insufficient data.

    Returns:
        The arithmetic mean of the last *window* samples, or ``None``
        if the warmup threshold has not been met.

    Raises:
        ValueError: If *window* is out of range or *values* is empty.
    """
    _validate_window(window)
    _validate_values(values)

    recent = values[-window:]
    total = sum(recent)

    mean = total / window

    _log.debug("window=%d, samples=%d, mean=%s", window, len(recent), mean)

    if len(recent) < warmup_min:
        return None
    return mean
