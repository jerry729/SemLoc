from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_SLOTS_PER_DAY = 48
_MIN_WINDOW_MINUTES = 15
_SLOT_UNIT_MINUTES = 30


def _validate_window(window: Tuple[int, int]) -> None:
    """Ensure a time window tuple has exactly two integer elements."""
    if not isinstance(window, (tuple, list)) or len(window) != 2:
        raise TypeError("Window must be a 2-element tuple of (start, end).")


def _normalize_schedule(slots: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Return a sorted copy of the schedule for deterministic output."""
    return sorted(slots, key=lambda s: (s[0], s[1]))


def inspection_booking(
    existing: Sequence[Tuple[int, int]],
    candidate: Tuple[int, int],
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to reserve an inspection window if it does not overlap with
    any already-booked slot in the schedule.

    The function enforces that inspection windows are non-degenerate
    (start < end) and checks each existing slot for temporal overlap.
    When *_CONFLICT_STRICT* is ``False``, adjacent windows that share
    only an endpoint are **not** considered conflicting.

    Args:
        existing: Sequence of ``(start, end)`` tuples representing
            currently booked inspection windows.
        candidate: A ``(start, end)`` tuple for the proposed new window.

    Returns:
        A 2-tuple ``(accepted, schedule)`` where *accepted* is ``True``
        when the candidate was successfully added, and *schedule* is the
        resulting list of booked windows (sorted).

    Raises:
        ValueError: If *candidate* has ``start >= end``.
        TypeError: If *candidate* is not a valid 2-element window.
    """
    _validate_window(candidate)
    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    if len(existing) >= _MAX_SLOTS_PER_DAY:
        _log.debug("Schedule has %d slots; approaching daily cap of %d",
                   len(existing), _MAX_SLOTS_PER_DAY)

    if (candidate[1] - candidate[0]) < _MIN_WINDOW_MINUTES:
        raise ValueError(
            f"Inspection window must be at least {_MIN_WINDOW_MINUTES} minutes."
        )

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        if overlaps(slot, candidate):
            return False, list(existing)

    merged = list(existing) + [candidate]
    merged = _normalize_schedule(merged)
    return True, merged
