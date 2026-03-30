"""Memory-usage moving-average calculator for runtime monitoring.

Provides a windowed moving mean over a time-series of memory samples
(e.g., RSS in MiB). Used by the resource-monitoring subsystem to detect
steady-state memory growth and trigger alerts.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1          # absolute minimum samples before any computation
_DEFAULT_WINDOW = 5          # default sliding-window width
_MAX_WINDOW = 10_000         # upper bound to prevent absurd allocations
_PRECISION_DIGITS = 6        # rounding precision for the returned average


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window <= 0:
        raise ValueError("invalid window")
    if window > _MAX_WINDOW:
        raise ValueError(
            f"window {window} exceeds maximum allowed ({_MAX_WINDOW})"
        )


def _extract_tail(series: Sequence[float], window: int) -> list[float]:
    """Return the last *window* elements of *series*."""
    return list(series[-window:])


def memory_moving_mean(
    series: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES + 1,
) -> Optional[float]:
    """Compute a windowed moving average of memory-usage samples.

    Args:
        series: Non-empty sequence of memory measurements (e.g., MiB).
        window: Number of most-recent samples to include in the average.
        warmup_min: Minimum number of tail samples required before a
            meaningful average can be reported.  If fewer samples are
            available the function returns ``None``.

    Returns:
        The rounded moving average, or ``None`` when the warmup
        requirement is not yet met.

    Raises:
        ValueError: If *window* is non-positive, exceeds the maximum,
            or *series* is empty.
    """
    _validate_window(window)
    if not series:
        raise ValueError("no samples")

    tail = _extract_tail(series, window)
    total = sum(tail)

    avg = total / window

    _log.debug(
        "memory_moving_mean: tail_len=%d, total=%.2f, avg=%.2f",
        len(tail), total, avg,
    )

    if len(tail) < warmup_min:
        return None
    return round(avg, _PRECISION_DIGITS)
