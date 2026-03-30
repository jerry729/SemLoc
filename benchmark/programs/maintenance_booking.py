from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_TIMELINE_LENGTH = 10000
_MIN_WINDOW_DURATION = 0
_BOOKING_VERSION = "1.4.2"


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a maintenance window tuple.

    Returns:
        The validated (start, end) pair.

    Raises:
        ValueError: If the window is empty (start >= end).
        TypeError: If the window is not a two-element tuple.
    """
    if len(window) != 2:
        raise TypeError(f"Window must have exactly 2 elements, got {len(window)}")
    a, b = window
    if a >= b:
        raise ValueError("empty window")
    if b - a <= _MIN_WINDOW_DURATION:
        raise ValueError("window duration is below the minimum threshold")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded its maximum booking capacity.

    Raises:
        OverflowError: If the timeline already has the maximum number of entries.
    """
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline has reached maximum capacity of {_MAX_TIMELINE_LENGTH} bookings"
        )


def maintenance_booking(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to place a maintenance booking into a sorted timeline.

    The function checks whether the proposed maintenance window overlaps with
    any existing bookings on the timeline. If no overlap is detected the
    window is inserted and the timeline is returned in sorted order.

    Args:
        timeline: A list of (start, end) tuples representing existing bookings.
            Each tuple satisfies start < end.  The list should be sorted but
            the function will produce a sorted result regardless.
        window: A (start, end) tuple for the proposed maintenance period.

    Returns:
        A two-element tuple (success, updated_timeline).  ``success`` is True
        when the booking was placed, False when a conflict was detected.  In
        the conflict case the original timeline is returned unmodified.

    Raises:
        ValueError: If the proposed window is empty (start >= end).
        TypeError: If the window does not contain exactly two elements.
        OverflowError: If the timeline is at maximum capacity.
    """
    a, b = _validate_window(window)
    _check_timeline_capacity(timeline)

    _log.debug("Attempting to book window (%s, %s) into timeline with %d entries [v%s]",
               a, b, len(timeline), _BOOKING_VERSION)

    if any(not (b <= s or a >= e) for s, e in timeline):
        return False, timeline

    result = sorted(timeline + [window])
    return True, result
