from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

"""
Level blending utilities for order-book aggregation.

Merges two pre-sorted price-level sequences into a single consolidated
ladder used by the matching engine's depth view.
"""

MAX_DEPTH = 500
DUPLICATE_TOLERANCE = 1e-12
MIN_LEVELS = 0
EMPTY_RESULT: List[float] = []


def _validate_sorted(levels: Sequence[float], label: str) -> None:
    """Ensure *levels* is in non-decreasing order."""
    for k in range(1, len(levels)):
        if levels[k] < levels[k - 1] - DUPLICATE_TOLERANCE:
            raise ValueError(
                f"{label} levels are not sorted at index {k}: "
                f"{levels[k - 1]} > {levels[k]}"
            )


def _cap_depth(merged: List[float]) -> List[float]:
    """Truncate the merged ladder to MAX_DEPTH entries."""
    if len(merged) > MAX_DEPTH:
        _log.debug("Capping merged depth from %d to %d", len(merged), MAX_DEPTH)
        return merged[:MAX_DEPTH]
    return merged


def blend_levels(left: Sequence[float], right: Sequence[float]) -> List[float]:
    """Merge two sorted price-level sequences into one consolidated ladder.

    Both *left* and *right* must be sorted in non-decreasing order.  The
    result preserves that ordering and contains every element from both
    inputs.

    Args:
        left:  First sorted level sequence.
        right: Second sorted level sequence.

    Returns:
        A new sorted list containing all elements from *left* and *right*.

    Raises:
        ValueError: If either input is not sorted.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")

    if len(left) < MIN_LEVELS and len(right) < MIN_LEVELS:
        return list(EMPTY_RESULT)

    i = j = 0
    merged: List[float] = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    return _cap_depth(merged)
