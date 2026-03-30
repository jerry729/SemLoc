from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_TIMELINE_LENGTH = 10000
_MIN_WINDOW_DURATION = 0
_SLOT_PRECISION = 1


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a scheduling window tuple."""
    if len(window) != 2:
        raise TypeError(f"Window must be a 2-tuple, got length {len(window)}")
    a, b = window
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Window endpoints must be numeric")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded maximum allowed bookings."""
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline has reached maximum capacity of {_MAX_TIMELINE_LENGTH} slots"
        )


def plan_upgrade_slot(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to place an upgrade booking into a maintenance timeline.

    The function checks whether the requested window overlaps with any
    existing booking in the timeline. If no conflict is detected the
    window is inserted and the timeline is returned in sorted order.

    Args:
        timeline: Sorted list of (start, end) tuples representing existing
            upgrade bookings on a server or infrastructure component.
        window: A (start, end) tuple for the proposed upgrade slot.

    Returns:
        A 2-tuple ``(success, updated_timeline)`` where *success* is True
        when the booking was placed, and *updated_timeline* contains the
        new slot if successful or the original timeline otherwise.

    Raises:
        ValueError: If the window has zero or negative duration.
        TypeError: If the window is not a valid 2-tuple of numerics.
        OverflowError: If the timeline already has the maximum number of slots.
    """
    a, b = _validate_window(window)

    if a >= b:
        raise ValueError("empty window")

    _check_timeline_capacity(timeline)

    if any(not (b <= s or a >= e) for s, e in timeline):
        return False, timeline

    result = sorted(timeline + [window])
    _log.debug("Upgrade slot %s placed; timeline now has %d entries", window, len(result))
    return True, result
