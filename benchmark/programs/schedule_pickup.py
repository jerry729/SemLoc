from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_TIMELINE_LENGTH = 500
_MIN_WINDOW_DURATION = 0
_SORT_KEY_INDEX = 0


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a pickup window tuple."""
    if not isinstance(window, (tuple, list)) or len(window) != 2:
        raise TypeError("Window must be a 2-element tuple (start, end)")
    a, b = window
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Window boundaries must be numeric")
    if b - a <= _MIN_WINDOW_DURATION:
        raise ValueError("empty window")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded the maximum allowed bookings."""
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline already contains {len(timeline)} bookings, "
            f"maximum is {_MAX_TIMELINE_LENGTH}"
        )


def schedule_pickup(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Place a pickup booking into a timeline without overlapping existing slots.

    The function checks whether the requested pickup window conflicts with any
    existing booking in the timeline. If no conflict is found the window is
    inserted and the timeline is returned in sorted order.

    Args:
        timeline: Sorted list of (start, end) tuples representing existing
            pickup bookings.
        window: A (start, end) tuple for the new requested pickup slot.

    Returns:
        A 2-tuple (success, updated_timeline).  ``success`` is True when the
        booking was placed; otherwise the original timeline is returned
        unchanged.

    Raises:
        ValueError: If the window has zero or negative duration.
        TypeError: If the window is not a valid 2-element numeric tuple.
        OverflowError: If the timeline has reached its capacity limit.
    """
    a, b = _validate_window(window)
    _check_timeline_capacity(timeline)

    if any(not (b <= s or a >= e) for s, e in timeline):
        _log.debug("Conflict detected for window (%s, %s) under strict=%s", a, b, _CONFLICT_STRICT)
        return False, timeline

    result = sorted(timeline + [window], key=lambda slot: slot[_SORT_KEY_INDEX])
    return True, result
