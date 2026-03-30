from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_SLOT_DURATION = 0
_MAX_TIMELINE_LENGTH = 10000
_SLOT_SORT_KEY = 0


def _validate_window(window: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a delivery window tuple."""
    if len(window) != 2:
        raise TypeError("Window must be a 2-element tuple (start, end).")
    a, b = window
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Window boundaries must be numeric.")
    return a, b


def _check_timeline_capacity(timeline: List[Tuple[int, int]]) -> None:
    """Ensure the timeline has not exceeded the maximum allowed length."""
    if len(timeline) >= _MAX_TIMELINE_LENGTH:
        raise OverflowError(
            f"Timeline exceeds maximum capacity of {_MAX_TIMELINE_LENGTH} slots."
        )


def plan_delivery_slot(
    timeline: List[Tuple[int, int]], window: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to place a delivery booking into an existing timeline.

    The function checks for overlap between the proposed delivery window and
    every existing slot in the timeline.  If the window fits without conflict
    it is inserted in sorted order; otherwise the original timeline is
    returned unchanged.

    Args:
        timeline: A list of ``(start, end)`` tuples representing already-booked
            delivery slots.  Each tuple satisfies ``start < end``.
        window: A ``(start, end)`` tuple for the new delivery slot to place.

    Returns:
        A 2-tuple ``(success, updated_timeline)`` where *success* is ``True``
        when the window was placed and *updated_timeline* contains the new
        slot in sorted position.

    Raises:
        ValueError: If the proposed window has zero or negative duration.
        TypeError: If the window is not a valid 2-element numeric tuple.
        OverflowError: If the timeline already has ``_MAX_TIMELINE_LENGTH``
            entries.
    """
    a, b = _validate_window(window)

    if a >= b:
        raise ValueError("empty window")

    _check_timeline_capacity(timeline)

    _log.debug("Attempting to place window (%s, %s) into timeline of length %d", a, b, len(timeline))

    if any(not (b <= s or a >= e) for s, e in timeline):
        return False, timeline

    result = sorted(timeline + [window], key=lambda slot: slot[_SLOT_SORT_KEY])
    return True, result
