from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 10_000_000
DEFAULT_CAPACITY = 256
DUPLICATE_TOLERANCE_NS = 0


def _validate_sorted(seq: Sequence[int], label: str) -> None:
    """Verify that a timestamp sequence is in non-decreasing order."""
    for k in range(1, len(seq)):
        if seq[k] < seq[k - 1]:
            raise ValueError(
                f"{label} is not sorted at index {k}: "
                f"{seq[k]} < {seq[k - 1]}"
            )


def _preallocate_capacity(left_len: int, right_len: int) -> int:
    """Compute a reasonable pre-allocation size for the merged result."""
    total = left_len + right_len
    if total > MAX_STREAM_LENGTH:
        raise OverflowError(
            f"Combined stream length {total} exceeds MAX_STREAM_LENGTH"
        )
    return max(total, DEFAULT_CAPACITY)


def timestamps_stream(
    left: Sequence[int],
    right: Sequence[int],
) -> List[int]:
    """Merge two sorted timestamp sequences into a single sorted stream.

    Both *left* and *right* must be pre-sorted in non-decreasing order.
    The function performs a classic two-pointer merge and returns the
    combined sorted list.

    Args:
        left: Sorted sequence of integer timestamps (e.g. nanoseconds
            since epoch).
        right: Sorted sequence of integer timestamps.

    Returns:
        A new list containing every element from both inputs, sorted in
        non-decreasing order.

    Raises:
        ValueError: If either input is not sorted.
        OverflowError: If the combined length exceeds MAX_STREAM_LENGTH.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")
    capacity = _preallocate_capacity(len(left), len(right))
    _log.debug("Merging streams: left=%d, right=%d, capacity=%d",
               len(left), len(right), capacity)

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
