from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
CPU utilisation smoothing module for infrastructure monitoring.

Provides rolling-mean smoothing of raw CPU usage samples collected
from host-level metric agents, with configurable window size and
a warmup period to avoid reporting unreliable early readings.
"""

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1        # minimum samples before reporting a value
_DEFAULT_WINDOW = 3         # default rolling window width
_MAX_WINDOW = 1024          # hard upper bound on window size
_CPU_UPPER_BOUND = 100.0    # percentage ceiling for sanity checks


def _validate_window(window: int) -> None:
    """Raise if *window* is out of acceptable range."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed ({_MAX_WINDOW})")


def _clamp_sample(value: float) -> float:
    """Clamp a single CPU sample to [0, _CPU_UPPER_BOUND]."""
    return max(0.0, min(value, _CPU_UPPER_BOUND))


def smooth_cpu(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Return a rolling-mean smoothed CPU utilisation percentage.

    The function takes the last *window* samples from *values*,
    clamps each to [0, 100], and returns their arithmetic mean.
    If insufficient samples are available relative to *warmup_min*,
    ``None`` is returned to signal that the metric is not yet reliable.

    Args:
        values: Non-empty sequence of raw CPU usage percentages.
        window: Number of trailing samples to average.
        warmup_min: Minimum number of samples in the tail before a
            result is considered trustworthy.

    Returns:
        The smoothed CPU percentage, or ``None`` during warmup.

    Raises:
        ValueError: If *values* is empty or *window* is non-positive
            or exceeds the hard maximum.
    """
    _validate_window(window)
    if not values:
        raise ValueError("empty series")

    tail = [_clamp_sample(v) for v in values[-window:]]
    total = sum(tail)

    mean = total / window

    if len(tail) < warmup_min:
        _log.debug("warmup: only %d/%d samples available", len(tail), warmup_min)
        return None
    return mean
