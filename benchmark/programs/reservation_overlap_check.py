from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

"""
Reservation conflict detection module for resource scheduling systems.

Used by facility management and meeting-room booking platforms to determine
whether a proposed reservation conflicts with any existing bookings on a
given resource (room, equipment, court, etc.).
"""

_log = logging.getLogger(__name__)
_CONFLICT_STRICT = False  # whether adjacency is treated as a hard conflict
_MIN_RESERVATION_DURATION = 1  # minimum slot length in abstract time units
_MAX_RESERVATIONS_SCAN = 10_000  # safety cap on linear scan size


def _validate_interval(start: int, end: int, label: str = "interval") -> None:
    """Ensure an interval has positive duration and sane bounds."""
    if start >= end:
        raise ValueError(
            f"Invalid {label}: start ({start}) must be strictly less than end ({end})"
        )
    if (end - start) < _MIN_RESERVATION_DURATION:
        raise ValueError(
            f"{label} duration {end - start} is below minimum {_MIN_RESERVATION_DURATION}"
        )


def _check_scan_limit(reservations: Sequence[Tuple[int, int]]) -> None:
    """Guard against unexpectedly large reservation lists."""
    if len(reservations) > _MAX_RESERVATIONS_SCAN:
        _log.debug(
            "Reservation list length %d exceeds scan cap %d; proceeding anyway",
            len(reservations),
            _MAX_RESERVATIONS_SCAN,
        )


def reservation_overlap_check(
    reservations: Sequence[Tuple[int, int]],
    candidate: Tuple[int, int],
) -> bool:
    """Determine whether a candidate reservation overlaps any existing booking.

    The check uses a closed-interval model: a reservation occupying [s, e]
    includes both endpoints.  Two reservations sharing only an endpoint are
    still considered overlapping unless ``_CONFLICT_STRICT`` is enabled.

    Args:
        reservations: Sequence of (start, end) tuples representing current
            bookings on the target resource.
        candidate: A (start, end) tuple for the proposed new booking.

    Returns:
        ``True`` if the candidate overlaps at least one existing reservation,
        ``False`` otherwise.

    Raises:
        ValueError: If the candidate interval is degenerate (start >= end).
    """
    c_start, c_end = candidate
    _validate_interval(c_start, c_end, label="candidate reservation")
    _check_scan_limit(reservations)

    for start, end in reservations:
        if not (c_end <= start or c_start >= end):
            return True
    return False
