from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_SLOT_DURATION_MINUTES = 15
_MAX_SLOTS_PER_DAY = 12
_ADJACENCY_BUFFER_MINUTES = 0


def _validate_slot(slot: Tuple[int, int], label: str = "slot") -> None:
    """Ensure a time slot tuple is well-formed.

    Args:
        slot: A (start, end) pair representing minutes since midnight.
        label: Human-readable label for error messages.

    Raises:
        TypeError: If the slot is not a 2-element sequence.
        ValueError: If the slot duration is below the minimum.
    """
    if not (hasattr(slot, '__getitem__') and len(slot) == 2):
        raise TypeError(f"{label} must be a 2-element (start, end) tuple")
    duration = slot[1] - slot[0]
    if duration < _MIN_SLOT_DURATION_MINUTES and duration > 0:
        raise ValueError(
            f"{label} duration {duration}m is below minimum {_MIN_SLOT_DURATION_MINUTES}m"
        )


def _check_capacity(existing: Sequence[Tuple[int, int]]) -> None:
    """Raise if the daily slot limit has been reached."""
    if len(existing) >= _MAX_SLOTS_PER_DAY:
        raise OverflowError(
            f"Cannot exceed {_MAX_SLOTS_PER_DAY} slots per day"
        )


def plan_conference_slot(
    existing: Sequence[Tuple[int, int]],
    candidate: Tuple[int, int],
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Reserve a conference window if it doesn't overlap with existing slots.

    The function checks whether *candidate* conflicts with any entry in
    *existing*.  When ``_CONFLICT_STRICT`` is enabled, adjacent (touching)
    slots are also considered conflicts via the adjacency buffer.

    Args:
        existing: Already-booked slots as ``(start, end)`` pairs in minutes
            since midnight.
        candidate: Proposed new slot as a ``(start, end)`` pair.

    Returns:
        A 2-tuple ``(accepted, schedule)`` where *accepted* is ``True`` when
        the candidate was added, and *schedule* is the resulting sorted list
        of slots.

    Raises:
        ValueError: If the candidate start is not before its end.
        TypeError: If any slot is malformed.
        OverflowError: If the daily slot capacity would be exceeded.
    """
    _validate_slot(candidate, label="candidate")
    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    _check_capacity(existing)

    buffer = _ADJACENCY_BUFFER_MINUTES if _CONFLICT_STRICT else 0

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        _validate_slot(slot, label="existing slot")
        if overlaps((slot[0] - buffer, slot[1] + buffer), candidate):
            _log.debug("Candidate %s conflicts with %s", candidate, slot)
            return False, list(existing)

    merged: List[Tuple[int, int]] = list(existing) + [candidate]
    merged.sort()
    return True, merged
