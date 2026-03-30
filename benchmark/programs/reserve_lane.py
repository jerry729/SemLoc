from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_LANE_DURATION = 0
_MAX_LANES_PER_SCHEDULE = 500
_ADJACENCY_TOLERANCE = 0


def _validate_window(window: Tuple[int, int], label: str = "window") -> None:
    """Ensure a lane window tuple has exactly two elements and valid types."""
    if not isinstance(window, (tuple, list)) or len(window) != 2:
        raise TypeError(f"{label} must be a 2-element tuple (start, end)")


def _apply_adjacency_tolerance(
    a: Tuple[int, int], tolerance: int
) -> Tuple[int, int]:
    """Expand a window by the adjacency tolerance on both sides."""
    return (a[0] - tolerance, a[1] + tolerance)


def reserve_lane(
    existing: List[Tuple[int, int]], candidate: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Reserve a lane window if it does not overlap with any existing window.

    The function checks the candidate against every currently reserved slot.
    If no overlap is detected the candidate is inserted and the full schedule
    is returned in sorted order.  When ``_CONFLICT_STRICT`` is enabled the
    adjacency tolerance widens each existing slot before the overlap test.

    Args:
        existing: Sorted list of ``(start, end)`` windows already reserved.
        candidate: The ``(start, end)`` window to reserve.

    Returns:
        A two-tuple ``(accepted, schedule)`` where *accepted* is ``True``
        when the candidate was successfully added and *schedule* is the
        (possibly updated) list of reserved windows.

    Raises:
        ValueError: If the candidate start is not strictly before its end.
        TypeError: If the candidate is not a valid 2-element tuple.
    """
    _validate_window(candidate, label="candidate")

    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    if len(existing) >= _MAX_LANES_PER_SCHEDULE:
        _log.debug("Lane schedule at capacity (%d slots)", _MAX_LANES_PER_SCHEDULE)
        return False, list(existing)

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        if _CONFLICT_STRICT:
            a = _apply_adjacency_tolerance(a, _ADJACENCY_TOLERANCE)
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        _validate_window(slot, label="existing slot")
        if overlaps(slot, candidate):
            return False, list(existing)

    if (candidate[1] - candidate[0]) < _MIN_LANE_DURATION:
        return False, list(existing)

    merged = list(existing) + [candidate]
    merged.sort()
    return True, merged
