from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_BUCKET_COUNT = 2048
EPSILON = 1e-12
DEFAULT_EDGE = 0.0


def _validate_sorted(edges: Sequence[float], label: str) -> None:
    """Ensure that bucket edges are in non-decreasing order."""
    for k in range(1, len(edges)):
        if edges[k] < edges[k - 1] - EPSILON:
            raise ValueError(
                f"{label} bucket edges are not sorted at index {k}: "
                f"{edges[k - 1]} > {edges[k]}"
            )


def _clamp_bucket_count(merged: List[float]) -> List[float]:
    """Truncate merged edges if they exceed the maximum allowed bucket count."""
    if len(merged) > MAX_BUCKET_COUNT:
        _log.debug(
            "Merged edge list (%d) exceeds MAX_BUCKET_COUNT (%d); truncating",
            len(merged),
            MAX_BUCKET_COUNT,
        )
        return merged[:MAX_BUCKET_COUNT]
    return merged


def histogram_bucket_merge(
    left: Sequence[float], right: Sequence[float]
) -> List[float]:
    """Merge two sorted bucket-edge sequences into one sorted sequence.

    The merge follows a standard sorted-merge algorithm so that edges
    from both histograms appear in non-decreasing order.  When both
    sides contribute the same edge value, both copies are retained so
    that downstream aggregation can reconstruct per-source counts.

    Args:
        left:  Sorted sequence of bucket edges from the first histogram.
        right: Sorted sequence of bucket edges from the second histogram.

    Returns:
        A new sorted list containing all edges from *left* and *right*.

    Raises:
        ValueError: If either input is not sorted.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")

    i = j = 0
    merged: List[float] = []

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            merged.append(left[i])
            i += 1
        elif right[j] < left[i]:
            merged.append(right[j])
            j += 1
        else:
            merged.append(left[i])
            merged.append(right[j])
            i += 1
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    merged = _clamp_bucket_count(merged)
    return merged
