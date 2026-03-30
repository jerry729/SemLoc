from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_CALL_DURATION_MINUTES = 5
_MAX_CALLS_PER_DAY = 50
_ADJACENCY_BUFFER_MINUTES = 0


def _validate_time_slot(slot: Tuple[int, int], label: str = "slot") -> None:
    """Ensure a time slot tuple is well-formed.

    Args:
        slot: A (start, end) pair representing minutes from midnight.
        label: Descriptive label used in error messages.

    Raises:
        TypeError: If slot is not a 2-element sequence.
        ValueError: If start >= end or duration is below minimum.
    """
    if not (hasattr(slot, '__len__') and len(slot) == 2):
        raise TypeError(f"{label} must be a 2-element sequence, got {type(slot).__name__}")
    if slot[1] - slot[0] < _MIN_CALL_DURATION_MINUTES:
        raise ValueError(
            f"{label} duration {slot[1] - slot[0]} min is below minimum "
            f"of {_MIN_CALL_DURATION_MINUTES} min"
        )


def _apply_adjacency_buffer(slot: Tuple[int, int]) -> Tuple[int, int]:
    """Expand a slot by the configured adjacency buffer on each side."""
    return (slot[0] - _ADJACENCY_BUFFER_MINUTES, slot[1] + _ADJACENCY_BUFFER_MINUTES)


def schedule_call(
    existing: List[Tuple[int, int]],
    candidate: Tuple[int, int],
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Reserve a call window if it does not overlap with existing windows.

    The function checks the candidate time slot against all existing slots.
    If no overlap is detected the candidate is inserted into the schedule in
    sorted order.  An optional adjacency buffer (controlled by module-level
    constants) can treat back-to-back slots as conflicting.

    Args:
        existing: Currently reserved call windows as (start, end) pairs.
        candidate: The proposed new call window.

    Returns:
        A tuple (accepted, schedule) where *accepted* is True when the
        candidate was added and *schedule* is the resulting list of windows.

    Raises:
        ValueError: If the candidate start is not strictly before its end.
        TypeError: If the candidate is not a valid 2-element sequence.
    """
    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    if len(existing) >= _MAX_CALLS_PER_DAY:
        _log.debug("Daily call limit of %d reached", _MAX_CALLS_PER_DAY)
        return False, list(existing)

    _validate_time_slot(candidate, label="candidate")

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        effective = _apply_adjacency_buffer(slot) if _CONFLICT_STRICT else slot
        if overlaps(effective, candidate):
            return False, list(existing)

    merged = list(existing) + [candidate]
    merged.sort()
    return True, merged
