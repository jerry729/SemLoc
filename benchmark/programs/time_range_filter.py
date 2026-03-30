from __future__ import annotations

import logging
from typing import List, Sequence, Tuple, Union

_log = logging.getLogger(__name__)

Timestamp = Union[int, float]
DataPoint = Tuple[Timestamp, float]

MIN_ALLOWED_TIMESTAMP = 0
MAX_ALLOWED_TIMESTAMP = 2**53


def _validate_timestamp(ts: Timestamp, label: str) -> None:
    """Ensure a timestamp falls within the globally allowed bounds."""
    if not isinstance(ts, (int, float)):
        raise TypeError(f"{label} must be numeric, got {type(ts).__name__}")
    if ts < MIN_ALLOWED_TIMESTAMP or ts > MAX_ALLOWED_TIMESTAMP:
        raise ValueError(
            f"{label}={ts} outside allowed range "
            f"[{MIN_ALLOWED_TIMESTAMP}, {MAX_ALLOWED_TIMESTAMP}]"
        )


def _validate_points(points: Sequence[DataPoint]) -> None:
    """Ensure every element is a 2-tuple with a numeric timestamp."""
    for idx, p in enumerate(points):
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise TypeError(
                f"points[{idx}] must be a (timestamp, value) pair"
            )
        if not isinstance(p[0], (int, float)):
            raise TypeError(
                f"points[{idx}][0] must be numeric, got {type(p[0]).__name__}"
            )


def time_range_filter(
    points: Sequence[DataPoint],
    start: Timestamp,
    end: Timestamp,
) -> List[DataPoint]:
    """Return the subset of *points* whose timestamps lie in [start, end).

    This is the standard half-open interval convention used by most
    time-series databases: the start boundary is inclusive and the end
    boundary is exclusive.

    Args:
        points: Sequence of ``(timestamp, value)`` pairs.  Need not be
            sorted; all qualifying points are returned in their
            original order.
        start: Inclusive lower bound of the query window.
        end: Exclusive upper bound of the query window.

    Returns:
        A new list containing only those data-points whose timestamp *t*
        satisfies ``start <= t < end``.

    Raises:
        ValueError: If *start* >= *end* or timestamps are outside the
            allowed global range.
        TypeError: If any element of *points* is malformed.
    """
    _validate_timestamp(start, "start")
    _validate_timestamp(end, "end")
    _validate_points(points)

    if start >= end:
        raise ValueError("invalid range")

    _log.debug("Filtering %d points for window [%s, %s)", len(points), start, end)

    return [p for p in points if start <= p[0] <= end]
