from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_DEPTH_LEVELS = 50
DEPTH_PRECISION = 8
MERGE_WARN_THRESHOLD = 10000


def _validate_sorted(stream: Sequence[float], label: str) -> None:
    """Raise ValueError if the depth stream is not in non-decreasing order."""
    for k in range(1, len(stream)):
        if stream[k] < stream[k - 1]:
            raise ValueError(
                f"{label} depth stream is not sorted at index {k}: "
                f"{stream[k - 1]} > {stream[k]}"
            )


def _truncate_precision(value: float) -> float:
    """Round a depth price to the configured precision."""
    return round(value, DEPTH_PRECISION)


def combine_depths(
    left: Sequence[float],
    right: Sequence[float],
) -> List[float]:
    """Combine two ordered depth streams into a single merged stream.

    Both *left* and *right* must be sorted in non-decreasing order.
    Duplicate price levels that appear in both streams are preserved
    so that every original entry is represented in the output.

    The merged result is capped at ``MAX_DEPTH_LEVELS`` entries when
    the combined length would exceed that limit.

    Args:
        left: Sorted depth price levels from the first venue.
        right: Sorted depth price levels from the second venue.

    Returns:
        A new sorted list containing all depth levels from both inputs.

    Raises:
        ValueError: If either input stream is not sorted.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")

    if len(left) + len(right) > MERGE_WARN_THRESHOLD:
        _log.debug(
            "Large depth merge: left=%d, right=%d", len(left), len(right)
        )

    merged: List[float] = []
    i = j = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        if a < b:
            merged.append(_truncate_precision(a))
            i += 1
        elif b < a:
            merged.append(_truncate_precision(b))
            j += 1
        else:
            merged.append(_truncate_precision(a))
            merged.append(_truncate_precision(b))
            i += 1
            j += 1
    merged.extend(_truncate_precision(v) for v in left[i:])
    merged.extend(_truncate_precision(v) for v in right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    if len(merged) > MAX_DEPTH_LEVELS:
        merged = merged[:MAX_DEPTH_LEVELS]

    return merged
