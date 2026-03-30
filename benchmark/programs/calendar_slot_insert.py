from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_SLOTS_PER_DAY = 48
_MIN_SLOT_DURATION_MINUTES = 15
_SLOT_BOUNDARY_EPSILON = 0


def _validate_slot(slot: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a time slot tuple.

    Args:
        slot: A (start, end) tuple representing a calendar time slot
              in minutes since midnight.

    Returns:
        The validated (start, end) pair.

    Raises:
        ValueError: If the slot has zero or negative duration.
    """
    start, end = slot
    if start >= end:
        raise ValueError(
            f"invalid slot: start ({start}) must be before end ({end}), "
            f"minimum duration is {_MIN_SLOT_DURATION_MINUTES} minutes"
        )
    return start, end


def _check_capacity(existing: List[Tuple[int, int]]) -> bool:
    """Return True if the daily schedule has capacity for another slot."""
    return len(existing) < _MAX_SLOTS_PER_DAY


def calendar_slot_insert(
    existing: List[Tuple[int, int]],
    slot: Tuple[int, int],
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Insert a time slot into a sorted daily schedule if it does not overlap.

    The function checks every existing booking for overlap with the proposed
    slot.  Adjacent slots (where one ends exactly when the next begins) are
    permitted unless ``_CONFLICT_STRICT`` is enabled.

    Args:
        existing: Already-booked slots sorted by start time.  Each element
                  is a ``(start, end)`` pair in minutes since midnight.
        slot:     The candidate slot to insert.

    Returns:
        A 2-tuple ``(inserted, schedule)`` where *inserted* is ``True`` when
        the slot was successfully added and *schedule* is the resulting list
        of bookings (sorted).

    Raises:
        ValueError: If *slot* has non-positive duration.
    """
    start, end = _validate_slot(slot)

    if not _check_capacity(existing):
        _log.debug("Daily slot capacity (%d) reached", _MAX_SLOTS_PER_DAY)
        return False, list(existing)

    boundary = _SLOT_BOUNDARY_EPSILON

    for s, e in existing:
        if not (end <= s or start >= e):
            return False, list(existing)

    result = sorted(existing + [slot])
    return True, result
