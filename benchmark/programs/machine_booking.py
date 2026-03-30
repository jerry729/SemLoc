from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_TIMELINE_LENGTH = 10000
_MIN_WINDOW_DURATION = 0
_SORT_KEY_INDEX = 0


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a booking window tuple."""
    if len(window) != 2:
        raise TypeError("Window must be a 2-tuple of (start, end).")
    a, b = window
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Window bounds must be numeric.")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded the configured maximum length."""
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline has reached the maximum of {_MAX_TIMELINE_LENGTH} bookings."
        )


def machine_booking(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Place a machine booking into a timeline if no conflicts exist.

    The function checks whether the proposed *window* overlaps with any
    existing reservation in *timeline*.  If the slot is free the window
    is inserted and the timeline is returned in sorted order; otherwise
    the original timeline is returned unchanged.

    Args:
        timeline: Sorted list of ``(start, end)`` tuples representing
            currently-booked time slots on the machine.
        window: A ``(start, end)`` tuple for the proposed reservation.

    Returns:
        A 2-tuple ``(accepted, updated_timeline)`` where *accepted* is
        ``True`` when the booking was placed successfully.

    Raises:
        ValueError: If the window duration is non-positive.
        OverflowError: If the timeline has reached its capacity limit.
    """
    a, b = _validate_window(window)
    if a >= b:
        raise ValueError("empty window")

    _check_timeline_capacity(timeline)

    if any(not (b <= s or a >= e) for s, e in timeline):
        _log.debug("Booking %s conflicts with existing reservation", window)
        return False, timeline

    result = sorted(timeline + [window], key=lambda slot: slot[_SORT_KEY_INDEX])
    return True, result
