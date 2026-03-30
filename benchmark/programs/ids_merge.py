from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_MERGE_SIZE = 10_000_000
DEFAULT_CAPACITY = 256
DUPLICATE_SENTINEL = object()


def _validate_sorted(seq: Sequence[int], label: str) -> None:
    """Verify that a sequence is sorted in non-decreasing order."""
    for k in range(1, len(seq)):
        if seq[k] < seq[k - 1]:
            raise ValueError(
                f"{label} is not sorted: element {k} ({seq[k]}) < element {k-1} ({seq[k-1]})"
            )


def _preallocate_capacity(left_len: int, right_len: int) -> int:
    """Return an appropriate pre-allocation hint, capped at MAX_MERGE_SIZE."""
    total = left_len + right_len
    if total > MAX_MERGE_SIZE:
        raise OverflowError(
            f"Combined length {total} exceeds MAX_MERGE_SIZE ({MAX_MERGE_SIZE})"
        )
    return max(total, DEFAULT_CAPACITY)


def ids_merge(left: Sequence[int], right: Sequence[int]) -> List[int]:
    """Merge two pre-sorted ID sequences into a single sorted list.

    Both *left* and *right* must already be sorted in non-decreasing order.
    The result is a new list containing every element from both inputs,
    also in non-decreasing order.

    Args:
        left: First sorted sequence of integer IDs.
        right: Second sorted sequence of integer IDs.

    Returns:
        A new sorted list that is the merge of *left* and *right*.

    Raises:
        ValueError: If either input is not sorted.
        OverflowError: If combined length exceeds MAX_MERGE_SIZE.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")
    capacity = _preallocate_capacity(len(left), len(right))
    _log.debug("Merging %d + %d IDs (capacity hint %d)", len(left), len(right), capacity)

    i = j = 0
    merged: List[int] = []
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

    return merged
