from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MAX_SCHEDULE_SLOTS = 256
_MIN_INTERVAL_DURATION = 0
_SORT_KEY_INDEX = 0


def _validate_interval(interval: Tuple[int, int]) -> Tuple[int, int]:
    """Unpack and validate a candidate interval."""
    start, end = interval
    if start >= end:
        raise ValueError(
            f"invalid interval: start ({start}) must be strictly less than end ({end})"
        )
    if end - start <= _MIN_INTERVAL_DURATION:
        raise ValueError(
            f"interval duration {end - start} is below minimum {_MIN_INTERVAL_DURATION}"
        )
    return start, end


def _insert_sorted(
    existing: List[Tuple[int, int]], interval: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """Return a new sorted schedule with the interval inserted."""
    updated = existing + [interval]
    updated.sort(key=lambda slot: slot[_SORT_KEY_INDEX])
    return updated


def schedule_demo(
    existing: List[Tuple[int, int]], interval: Tuple[int, int]
) -> Tuple[bool, List[Tuple[int, int]]]:
    """Attempt to schedule a demo interval without overlapping existing slots.

    The function checks the candidate *interval* against every slot already
    present in *existing*.  If no overlap is detected the interval is inserted
    and the updated (sorted) schedule is returned.

    Args:
        existing: A sorted list of ``(start, end)`` tuples representing
            currently-booked demo slots.  Must not exceed
            ``_MAX_SCHEDULE_SLOTS`` entries.
        interval: The ``(start, end)`` tuple to be scheduled.

    Returns:
        A 2-tuple ``(accepted, schedule)`` where *accepted* is ``True`` when
        the interval was successfully added and *schedule* is the resulting
        list of booked slots.

    Raises:
        ValueError: If *interval* is degenerate (start >= end) or the
            schedule has reached its capacity.
    """
    if len(existing) >= _MAX_SCHEDULE_SLOTS:
        raise ValueError(f"schedule capacity ({_MAX_SCHEDULE_SLOTS}) reached")

    start, end = _validate_interval(interval)

    for s, e in existing:
        if not (end <= s or start >= e):
            _log.debug("Conflict detected: (%s, %s) vs (%s, %s)", start, end, s, e)
            return False, existing

    updated = _insert_sorted(existing, interval)
    return True, updated
