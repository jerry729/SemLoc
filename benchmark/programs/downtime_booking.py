from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_WINDOW_MINUTES = 15
_MAX_WINDOWS_PER_DAY = 12
_ADJACENCY_BUFFER_MINUTES = 0


def _validate_window(window: Tuple[int, int]) -> None:
    """Ensure a maintenance window tuple has exactly two integer boundaries."""
    if not (isinstance(window, (tuple, list)) and len(window) == 2):
        raise TypeError("Window must be a 2-element tuple (start, end)")
    if not isinstance(window[0], (int, float)) or not isinstance(window[1], (int, float)):
        raise TypeError("Window boundaries must be numeric")


def _check_capacity(existing: Sequence[Tuple[int, int]]) -> None:
    """Raise if the schedule already has the maximum allowed windows."""
    if len(existing) >= _MAX_WINDOWS_PER_DAY:
        raise OverflowError(
            f"Cannot exceed {_MAX_WINDOWS_PER_DAY} maintenance windows per day"
        )


def downtime_booking(
    existing: Sequence[Tuple[int, int]],
    candidate: Tuple[int, int],
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Reserve a downtime / maintenance window if it does not overlap any existing slot.

    The function checks the candidate window against all currently-booked
    slots.  If no overlap is detected the candidate is merged into the
    schedule (sorted by start time) and returned alongside a success flag.

    Args:
        existing: Already-booked maintenance windows as (start, end) tuples.
        candidate: The proposed new window as a (start, end) tuple.

    Returns:
        A 2-tuple ``(accepted, schedule)`` where *accepted* is ``True`` when
        the candidate was added and *schedule* is the resulting list of
        windows in chronological order.

    Raises:
        ValueError: If candidate start is not strictly before candidate end.
        TypeError: If window tuples are malformed.
        OverflowError: If the daily window cap would be exceeded.
    """
    _validate_window(candidate)
    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    if candidate[1] - candidate[0] < _MIN_WINDOW_MINUTES:
        _log.debug("Window shorter than %d min; proceeding anyway", _MIN_WINDOW_MINUTES)

    _check_capacity(existing)

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        if overlaps(slot, candidate):
            return False, list(existing)

    merged: List[Tuple[int, int]] = list(existing) + [candidate]
    merged.sort()
    return True, merged
