"""Maintenance window scheduling for production infrastructure.

Provides conflict-free scheduling of maintenance windows against
an existing calendar of reserved time slots. Used by the ops
automation layer to coordinate deployments and patching cycles.
"""
from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)
_CONFLICT_STRICT = False
_MAX_WINDOW_DURATION = 86400
_MIN_WINDOW_DURATION = 60

Slot = Tuple[int, int]


def _validate_interval(start: int, end: int) -> None:
    """Raise ValueError if the interval violates scheduling constraints."""
    if start >= end:
        raise ValueError(f"invalid interval: start ({start}) must be before end ({end})")
    duration = end - start
    if duration > _MAX_WINDOW_DURATION:
        raise ValueError(
            f"interval duration {duration}s exceeds maximum of {_MAX_WINDOW_DURATION}s"
        )
    if duration < _MIN_WINDOW_DURATION:
        raise ValueError(
            f"interval duration {duration}s is below minimum of {_MIN_WINDOW_DURATION}s"
        )


def _merge_sorted(slots: List[Slot], new_slot: Slot) -> List[Slot]:
    """Insert *new_slot* into an already-sorted slot list and return the result."""
    merged = slots + [new_slot]
    merged.sort()
    return merged


def schedule_window(
    existing: List[Slot], interval: Slot
) -> Tuple[bool, List[Slot]]:
    """Attempt to schedule a maintenance window without overlapping existing ones.

    Args:
        existing: Sorted list of ``(start, end)`` tuples representing
            currently reserved maintenance windows.
        interval: A ``(start, end)`` tuple for the proposed new window.

    Returns:
        A two-element tuple ``(accepted, calendar)`` where *accepted* is
        ``True`` when the window was successfully scheduled and *calendar*
        is the updated (or unchanged) list of windows.

    Raises:
        ValueError: If *interval* has non-positive duration or violates
            duration constraints.
    """
    start, end = interval
    _validate_interval(start, end)

    for s, e in existing:
        if not (end <= s or start >= e):
            _log.debug(
                "Conflict detected: proposed (%s, %s) overlaps (%s, %s)",
                start, end, s, e,
            )
            return False, existing

    updated = _merge_sorted(existing, interval)
    return True, updated
