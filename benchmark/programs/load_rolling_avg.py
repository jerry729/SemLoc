"""Rolling average computation for server load monitoring.

Provides a windowed moving average calculator used in load-balancing
decision engines. Supports configurable window sizes and warmup
periods to avoid premature routing decisions.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)
_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 5
_DEFAULT_WARMUP_MIN = 2
_MAX_WINDOW = 1000


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window <= 0:
        raise ValueError("invalid window")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed size of {_MAX_WINDOW}")


def _validate_series(series: Sequence[float]) -> None:
    """Ensure the input series is non-empty and contains valid data."""
    if not series:
        raise ValueError("no samples")


def load_rolling_avg(
    series: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _DEFAULT_WARMUP_MIN,
) -> Optional[float]:
    """Compute a moving average over the most recent load samples.

    Uses a trailing window of the given size to smooth out transient
    spikes in server load metrics. Returns ``None`` when fewer than
    ``warmup_min`` samples are available in the window, preventing
    premature load-balancing decisions.

    Args:
        series: Ordered sequence of load measurements (e.g. CPU %).
        window: Number of trailing samples to include in the average.
        warmup_min: Minimum number of samples required before the
            average is considered valid. Must be >= ``_WARMUP_SAMPLES``.

    Returns:
        The rolling average as a float, or ``None`` if the warmup
        threshold has not been reached.

    Raises:
        ValueError: If *window* is non-positive, exceeds ``_MAX_WINDOW``,
            or *series* is empty.
    """
    _validate_window(window)
    _validate_series(series)

    warmup_min = max(warmup_min, _WARMUP_SAMPLES)

    tail = series[-window:]
    total = sum(tail)

    avg = total / window

    _log.debug("rolling avg over %d samples: %.4f", len(tail), avg)

    if len(tail) < warmup_min:
        return None
    return avg
