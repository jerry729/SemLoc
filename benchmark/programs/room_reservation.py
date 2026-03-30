from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_DURATION_MINUTES = 15
_MAX_RESERVATIONS_PER_DAY = 50
_TIME_UNIT = "minutes"


def _validate_interval(start: int, end: int) -> None:
    """Ensure the interval meets minimum duration and ordering constraints."""
    if start >= end:
        raise ValueError(
            f"Invalid interval: start ({start}) must be strictly less than end ({end})"
        )
    duration = end - start
    if duration < _MIN_DURATION_MINUTES:
        raise ValueError(
            f"Interval duration {duration} {_TIME_UNIT} is below the minimum "
            f"of {_MIN_DURATION_MINUTES} {_TIME_UNIT}"
        )


def _check_capacity(existing: List[Tuple[int, int]]) -> None:
    """Raise if the daily reservation cap has been reached."""
    if len(existing) >= _MAX_RESERVATIONS_PER_DAY:
        raise OverflowError(
            f"Room has reached the maximum of {_MAX_RESERVATIONS_PER_DAY} "
            f"reservations per day"
        )


def room_reservation(
    existing: List[Tuple[int, int]], interval: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to schedule a room interval without overlapping existing bookings.

    The function checks whether the proposed *interval* conflicts with any
    reservation already present in *existing*.  If no conflict is found the
    interval is inserted and the updated (sorted) schedule is returned.

    Args:
        existing: A sorted list of ``(start, end)`` tuples representing
            currently confirmed reservations, measured in minutes from
            midnight.
        interval: A ``(start, end)`` tuple for the proposed reservation.

    Returns:
        A two-element tuple ``(accepted, schedule)`` where *accepted* is
        ``True`` when the reservation was added, and *schedule* is the
        (possibly updated) list of reservations.

    Raises:
        ValueError: If the interval is degenerate or shorter than the
            configured minimum duration.
        OverflowError: If the room already has the maximum number of
            reservations for the day.
    """
    start, end = interval
    _validate_interval(start, end)
    _check_capacity(existing)

    _log.debug("Checking interval (%d, %d) against %d existing bookings", start, end, len(existing))

    for s, e in existing:
        if not (end <= s or start >= e):
            return False, existing

    updated = existing + [interval]
    updated.sort()
    return True, updated
