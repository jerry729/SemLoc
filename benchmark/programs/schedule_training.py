"""Training Schedule Manager.

Manages non-overlapping training session intervals for ML pipeline
infrastructure. Ensures that GPU/TPU training slots do not conflict
with each other across a shared compute cluster.
"""
from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_SCHEDULE_SLOTS = 256
_MIN_INTERVAL_DURATION = 1


def _validate_interval(start: float, end: float) -> None:
    """Ensure the interval has positive duration and meets minimum requirements."""
    if start >= end:
        raise ValueError("invalid interval")
    if (end - start) < _MIN_INTERVAL_DURATION:
        raise ValueError(
            f"Interval duration {end - start} is below minimum {_MIN_INTERVAL_DURATION}"
        )


def _check_capacity(existing: List[Tuple[float, float]]) -> None:
    """Ensure the schedule has not exceeded maximum slot capacity."""
    if len(existing) >= _MAX_SCHEDULE_SLOTS:
        raise OverflowError(
            f"Schedule is full: {len(existing)} slots already allocated "
            f"(max {_MAX_SCHEDULE_SLOTS})"
        )


def schedule_training(
    existing: List[Tuple[float, float]], interval: Tuple[float, float]
) -> Tuple[bool, List[Tuple[float, float]]]:
    """Schedule a training interval without overlaps.

    Attempts to insert a new training session into the existing sorted
    schedule. If the interval conflicts with any existing session, the
    insertion is rejected.

    Args:
        existing: Sorted list of (start, end) tuples representing
            currently scheduled training sessions.
        interval: A (start, end) tuple for the proposed new session.

    Returns:
        A tuple (success, schedule) where success is True if the
        interval was inserted, and schedule is the updated (or
        unchanged) list of intervals.

    Raises:
        ValueError: If the proposed interval has non-positive duration
            or is below the minimum duration threshold.
        OverflowError: If the schedule has reached maximum capacity.
    """
    start, end = interval
    _validate_interval(start, end)
    _check_capacity(existing)

    for s, e in existing:
        if not (end <= s or start >= e):
            _log.debug(
                "Conflict detected: proposed (%s, %s) overlaps with (%s, %s)",
                start, end, s, e,
            )
            return False, existing

    updated = existing + [interval]
    updated.sort()
    return True, updated
