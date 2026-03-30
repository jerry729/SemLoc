from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 10_000_000
DEFAULT_SENTINEL = float('inf')
MERGE_LOG_THRESHOLD = 1000


def _validate_sorted(seq: Sequence[float], label: str) -> None:
    """Verify that a signal sequence is sorted in non-decreasing order."""
    for k in range(1, len(seq)):
        if seq[k] < seq[k - 1]:
            raise ValueError(
                f"Signal sequence '{label}' is not sorted at index {k}: "
                f"{seq[k - 1]} > {seq[k]}"
            )


def _check_length(left: Sequence[float], right: Sequence[float]) -> None:
    """Ensure combined length does not exceed the platform limit."""
    total = len(left) + len(right)
    if total > MAX_STREAM_LENGTH:
        raise OverflowError(
            f"Combined stream length {total} exceeds MAX_STREAM_LENGTH "
            f"({MAX_STREAM_LENGTH})"
        )


def signals_stream(left: Sequence[float], right: Sequence[float]) -> List[float]:
    """Merge two sorted signal sequences into a single sorted sequence.

    Performs a standard two-pointer merge of pre-sorted numeric streams,
    preserving duplicate values and maintaining overall sort order.

    Args:
        left: A non-decreasing sequence of signal values.
        right: A non-decreasing sequence of signal values.

    Returns:
        A new list containing all elements from *left* and *right* in
        non-decreasing order.

    Raises:
        ValueError: If either input sequence is not sorted.
        OverflowError: If the combined length exceeds MAX_STREAM_LENGTH.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")
    _check_length(left, right)

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

    if len(merged) >= MERGE_LOG_THRESHOLD:
        _log.debug("Merged stream contains %d signals", len(merged))

    return merged
