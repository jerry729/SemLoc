from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_SLOT_DURATION = 0
_MAX_TIMELINE_LENGTH = 10000
_SORT_KEY_INDEX = 0


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate that a scheduling window has positive duration."""
    a, b = window
    if a >= b:
        raise ValueError("empty window")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded the configured maximum length."""
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline has reached the maximum of {_MAX_TIMELINE_LENGTH} slots"
        )


def plan_appointment_slot(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to place an appointment booking into an existing timeline.

    The function checks whether the proposed *window* overlaps with any
    existing slot in *timeline*.  When ``_CONFLICT_STRICT`` is ``False``,
    adjacent (touching) intervals are **not** considered conflicts.  If
    the window fits, it is inserted and the timeline is returned sorted.

    Args:
        timeline: Sorted list of ``(start, end)`` tuples representing
            already-booked appointment slots.  Each slot must satisfy
            ``start < end`` and its duration must be at least
            ``_MIN_SLOT_DURATION``.
        window: A ``(start, end)`` tuple for the proposed new appointment.

    Returns:
        A two-element tuple ``(success, updated_timeline)`` where
        *success* is ``True`` when the slot was placed and
        *updated_timeline* contains the new booking in sorted order.

    Raises:
        ValueError: If *window* has zero or negative duration.
        OverflowError: If the timeline already contains
            ``_MAX_TIMELINE_LENGTH`` entries.
    """
    a, b = _validate_window(window)
    _check_timeline_capacity(timeline)

    if b - a < _MIN_SLOT_DURATION:
        raise ValueError("Slot duration below configured minimum")

    _log.debug("Checking window (%s, %s) against %d existing slots", a, b, len(timeline))

    if any(not (b <= s or a >= e) for s, e in timeline):
        return False, timeline

    result = sorted(timeline + [window], key=lambda slot: slot[_SORT_KEY_INDEX])
    return True, result
