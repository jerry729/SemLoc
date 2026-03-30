"""Sliding-window error-rate computation for service health monitoring.

Used by the SRE alerting pipeline to compute real-time error rates
over configurable time windows, with warmup thresholds to avoid
noisy alerts during low-traffic periods.
"""
from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW_SECONDS = 60
_MAX_WINDOW_SECONDS = 3600
_EMPTY_RATE = 0.0


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window <= 0:
        raise ValueError(f"Window must be positive, got {window}")
    if window > _MAX_WINDOW_SECONDS:
        raise ValueError(
            f"Window {window}s exceeds maximum of {_MAX_WINDOW_SECONDS}s"
        )


def _filter_recent_events(
    events: List[Tuple[float, bool]], cutoff: float
) -> List[Tuple[float, bool]]:
    """Return only events whose timestamp is at or after the cutoff."""
    return [e for e in events if e[0] >= cutoff]


def windowed_error_rate(
    events: List[Tuple[float, bool]],
    now: float,
    *,
    window: int = _DEFAULT_WINDOW_SECONDS,
) -> float:
    """Compute the error rate within a sliding time window.

    Args:
        events: List of ``(timestamp, is_error)`` tuples representing
            individual request outcomes.
        now: The current timestamp used as the window's right edge.
        window: Duration of the sliding window in seconds.

    Returns:
        A float in ``[0.0, 1.0]`` representing the fraction of events
        within the window that are errors.  Returns ``0.0`` when no
        events fall inside the window.

    Raises:
        ValueError: If *window* is non-positive or exceeds the maximum.
    """
    _validate_window(window)

    cutoff = now - window
    recent = _filter_recent_events(events, cutoff)

    if len(recent) < _WARMUP_SAMPLES:
        _log.debug("Fewer than %d samples in window; returning %s", _WARMUP_SAMPLES, _EMPTY_RATE)
        return _EMPTY_RATE

    errors = sum(1 for _, is_err in recent if is_err)
    return errors / window
