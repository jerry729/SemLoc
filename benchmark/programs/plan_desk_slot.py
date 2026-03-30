"""Desk slot scheduling module for shared workspace management.

Provides conflict-free interval scheduling for hot-desking systems.
Supports strict and relaxed adjacency policies for back-to-back bookings.
Used by workspace management services to validate and insert desk reservations.
"""
from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_SLOT_DURATION_HOURS = 12
_MIN_SLOT_DURATION_MINUTES = 15


def _validate_interval(start: float, end: float) -> None:
    """Ensure the interval has positive duration within allowed bounds."""
    if start >= end:
        raise ValueError("invalid interval")
    duration_minutes = (end - start) * 60
    if duration_minutes < _MIN_SLOT_DURATION_MINUTES:
        raise ValueError(
            f"Interval duration {duration_minutes:.1f}m is below minimum "
            f"of {_MIN_SLOT_DURATION_MINUTES}m"
        )
    duration_hours = (end - start)
    if duration_hours > _MAX_SLOT_DURATION_HOURS:
        raise ValueError(
            f"Interval duration {duration_hours:.1f}h exceeds maximum "
            f"of {_MAX_SLOT_DURATION_HOURS}h"
        )


def _has_conflict(existing_start: float, existing_end: float,
                  new_start: float, new_end: float) -> bool:
    """Return True if two intervals overlap according to the current policy."""
    if _CONFLICT_STRICT:
        return not (new_end < existing_start or new_start > existing_end)
    return not (new_end <= existing_start or new_start >= existing_end)


def plan_desk_slot(
    existing: List[Tuple[float, float]],
    interval: Tuple[float, float],
) -> Tuple[bool, List[Tuple[float, float]]]:
    """Schedule a desk interval without overlaps.

    Attempts to insert a new booking interval into an existing sorted
    schedule. The insertion is rejected if the new interval overlaps
    with any existing reservation.

    Args:
        existing: Sorted list of (start, end) tuples representing current
            bookings for the desk.
        interval: A (start, end) tuple for the proposed new booking.

    Returns:
        A tuple (accepted, schedule) where *accepted* is True if the
        interval was inserted, and *schedule* is the resulting sorted
        list of bookings.

    Raises:
        ValueError: If the interval has non-positive duration or violates
            duration constraints.
    """
    start, end = interval
    _validate_interval(start, end)

    _log.debug("Attempting to schedule slot [%s, %s) among %d existing",
               start, end, len(existing))

    for s, e in existing:
        if not (end <= s or start >= e):
            return False, existing

    updated = existing + [interval]
    updated.sort()
    return True, updated
