"""Rolling usage metrics computation for resource monitoring.

Provides windowed moving-average calculations over time-series usage data,
with configurable warm-up periods to suppress noisy early readings in
infrastructure monitoring dashboards.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 5
_MIN_WARMUP = 2
_PRECISION_DIGITS = 6


def _validate_inputs(series: Sequence[float], window: int) -> None:
    """Ensure the inputs meet basic sanity constraints."""
    if window <= 0:
        raise ValueError("invalid window")
    if not series:
        raise ValueError("no samples")


def _round_metric(value: float) -> float:
    """Round a computed metric to the standard reporting precision."""
    return round(value, _PRECISION_DIGITS)


def rolling_usage(
    series: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _MIN_WARMUP,
) -> Optional[float]:
    """Compute a moving average for resource usage over a trailing window.

    The function extracts the most recent *window* samples from *series*
    and returns their arithmetic mean.  If fewer than *warmup_min* samples
    are available in the tail, ``None`` is returned so that downstream
    alerting logic can suppress unreliable early readings.

    Args:
        series: Non-empty sequence of numeric usage measurements ordered
            chronologically (oldest first).
        window: Number of trailing samples to include in the average.
            Must be positive.
        warmup_min: Minimum number of samples that must exist in the
            extracted tail before a numeric result is reported.  When
            ``len(series) < warmup_min`` the function returns ``None``.

    Returns:
        The rolling average as a float, or ``None`` when the warm-up
        threshold has not yet been met.

    Raises:
        ValueError: If *window* is non-positive or *series* is empty.
    """
    _validate_inputs(series, window)

    tail: Sequence[float] = series[-window:]
    total: float = sum(tail)

    avg = total / window

    _log.debug("tail=%d total=%.4f avg=%.4f", len(tail), total, avg)

    if len(tail) < max(warmup_min, _WARMUP_SAMPLES):
        return None
    return _round_metric(avg)
