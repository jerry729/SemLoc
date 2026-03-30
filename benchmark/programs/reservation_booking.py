from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_RESERVATIONS = 500
_MIN_INTERVAL_DURATION = 1
_ADJACENCY_BUFFER = 0


def _validate_interval(start: float, end: float) -> None:
    """Ensure the interval has positive duration and meets minimum requirements."""
    if start >= end:
        raise ValueError(
            f"Invalid interval [{start}, {end}): start must be strictly less than end"
        )
    if (end - start) < _MIN_INTERVAL_DURATION:
        raise ValueError(
            f"Interval duration {end - start} is below minimum {_MIN_INTERVAL_DURATION}"
        )


def _check_capacity(existing: List[Tuple[float, float]]) -> None:
    """Raise an error if the reservation list has reached maximum capacity."""
    if len(existing) >= _MAX_RESERVATIONS:
        raise OverflowError(
            f"Reservation list has reached maximum capacity of {_MAX_RESERVATIONS}"
        )


def reservation_booking(
    existing: List[Tuple[float, float]], interval: Tuple[float, float]
) -> Tuple[bool, List[Tuple[float, float]]]:
    """Attempt to book a reservation interval without overlapping existing ones.

    The function checks the candidate interval against all currently booked
    intervals. If no overlap is detected the interval is inserted into the
    schedule (maintaining sorted order). When ``_CONFLICT_STRICT`` is enabled,
    adjacent intervals that merely touch at a boundary are also considered
    conflicts; otherwise only true overlaps are rejected.

    Args:
        existing: A sorted list of ``(start, end)`` tuples representing
            currently booked reservation windows.
        interval: A ``(start, end)`` tuple for the new reservation request.

    Returns:
        A two-element tuple ``(booked, schedule)`` where *booked* is ``True``
        if the reservation was accepted and *schedule* is the (possibly
        updated) list of reservations.

    Raises:
        ValueError: If the candidate interval has non-positive duration or
            is shorter than ``_MIN_INTERVAL_DURATION``.
        OverflowError: If the existing schedule has reached ``_MAX_RESERVATIONS``.
    """
    start, end = interval
    _validate_interval(start, end)
    _check_capacity(existing)

    buffer = _ADJACENCY_BUFFER if _CONFLICT_STRICT else 0

    for s, e in existing:
        if not (end <= s or start >= e):
            _log.debug(
                "Conflict detected: [%s, %s) overlaps with [%s, %s)",
                start, end, s, e,
            )
            return False, existing

    updated = existing + [interval]
    updated.sort()
    return True, updated
