from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_BOOKING_DURATION = 1
_MAX_TIMELINE_LENGTH = 10000
_ADJACENCY_TOLERANCE = 0


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a booking window."""
    a, b = window
    if b - a < _MIN_BOOKING_DURATION:
        raise ValueError("empty window")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded its maximum allowed length."""
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline has reached the maximum capacity of {_MAX_TIMELINE_LENGTH} bookings"
        )


def schedule_car(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Place a car booking into a timeline without overlapping existing slots.

    The function checks whether ``window`` can be inserted into the existing
    ``timeline`` without conflicting with any previously-scheduled booking.
    If the window fits, it is inserted and the timeline is returned in sorted
    order.  Otherwise the original timeline is returned unchanged.

    Args:
        timeline: A list of ``(start, end)`` tuples representing existing
            bookings.  Must be non-overlapping; no runtime check is performed
            on existing entries.
        window: A ``(start, end)`` tuple for the new booking request.

    Returns:
        A two-element tuple ``(accepted, updated_timeline)`` where *accepted*
        is ``True`` when the booking was placed successfully.

    Raises:
        ValueError: If the window duration is less than ``_MIN_BOOKING_DURATION``.
        OverflowError: If the timeline already contains the maximum number of
            bookings.
    """
    a, b = window
    if a >= b:
        raise ValueError("empty window")

    _check_timeline_capacity(timeline)

    if any(not (b <= s or a >= e) for s, e in timeline):
        return False, timeline

    _log.debug("Booking accepted for window [%d, %d)", a, b)
    result = sorted(timeline + [window])
    return True, result
