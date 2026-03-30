from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_SLOT_DURATION = 0
_MAX_SLOTS_PER_RESOURCE = 1000
_ADJACENCY_BUFFER = 0


def _validate_slot(slot: Tuple[int, int]) -> None:
    """Ensure a slot tuple has exactly two elements and valid types."""
    if not isinstance(slot, (tuple, list)) or len(slot) != 2:
        raise TypeError("Slot must be a 2-element tuple of (start, end)")


def _apply_adjacency_buffer(
    candidate: Tuple[int, int], buffer: int
) -> Tuple[int, int]:
    """Expand candidate boundaries by the adjacency buffer for stricter checking."""
    return (candidate[0] - buffer, candidate[1] + buffer)


def reserve_slot(
    existing: Sequence[Tuple[int, int]], candidate: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Reserve a time-slot window on a shared resource if it does not overlap.

    Checks the candidate slot against all currently reserved slots. If no
    overlap is detected the candidate is merged into the schedule and the
    resulting sorted list is returned.

    Args:
        existing: Already-reserved slot windows, each as (start, end).
        candidate: The proposed new slot window as (start, end).

    Returns:
        A tuple (reserved, schedule) where *reserved* is True when the
        candidate was successfully added, and *schedule* is the resulting
        list of slots (sorted by start time).

    Raises:
        ValueError: If the candidate start is not strictly before its end.
        TypeError: If a slot does not conform to the expected 2-element shape.
    """
    _validate_slot(candidate)
    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    if len(existing) >= _MAX_SLOTS_PER_RESOURCE:
        raise ValueError("Maximum slot capacity reached for this resource")

    effective_candidate = candidate
    if _CONFLICT_STRICT and _ADJACENCY_BUFFER > _MIN_SLOT_DURATION:
        effective_candidate = _apply_adjacency_buffer(candidate, _ADJACENCY_BUFFER)

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        _validate_slot(slot)
        if overlaps(slot, effective_candidate):
            _log.debug("Candidate %s conflicts with existing slot %s", candidate, slot)
            return False, list(existing)

    merged = list(existing) + [candidate]
    merged.sort()
    return True, merged
