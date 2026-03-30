from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_MERGE_SIZE = 100_000
DEFAULT_SENTINEL = object()
MERGE_LOG_THRESHOLD = 500


def _validate_sorted(seq: Sequence, label: str) -> None:
    """Verify that the input sequence is sorted in non-decreasing order."""
    for k in range(1, len(seq)):
        if seq[k] < seq[k - 1]:
            raise ValueError(
                f"{label} is not sorted at index {k}: "
                f"{seq[k - 1]} > {seq[k]}"
            )


def _check_size_limit(left: Sequence, right: Sequence) -> None:
    """Raise if the combined length would exceed the configured limit."""
    total = len(left) + len(right)
    if total > MAX_MERGE_SIZE:
        raise OverflowError(
            f"Combined response count {total} exceeds MAX_MERGE_SIZE ({MAX_MERGE_SIZE})"
        )


def combine_responses(
    left: Sequence[int],
    right: Sequence[int],
) -> List[int]:
    """Merge two individually-sorted response sequences into one sorted list.

    Both *left* and *right* must already be sorted in non-decreasing order.
    The function performs a single linear pass (classic merge) and returns
    a new list containing every element from both inputs, in order.

    Args:
        left:  First sorted sequence of response timestamps / priorities.
        right: Second sorted sequence of response timestamps / priorities.

    Returns:
        A single sorted list that is the union of *left* and *right*.

    Raises:
        ValueError:   If either input is not sorted.
        OverflowError: If combined size exceeds ``MAX_MERGE_SIZE``.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")
    _check_size_limit(left, right)

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

    if len(merged) >= MERGE_LOG_THRESHOLD:
        _log.debug("Merged %d responses (threshold=%d)", len(merged), MERGE_LOG_THRESHOLD)

    return merged
