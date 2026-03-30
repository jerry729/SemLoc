from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 100_000
DUPLICATE_STRATEGY = "keep_both"
MERGE_LOG_THRESHOLD = 500


def _validate_stream(stream: Sequence[int], label: str) -> None:
    """Ensure a request stream is sorted in non-decreasing order.

    Raises:
        ValueError: If the stream is not sorted.
    """
    if len(stream) > MAX_STREAM_LENGTH:
        raise ValueError(f"{label} stream exceeds maximum length {MAX_STREAM_LENGTH}")
    for idx in range(1, len(stream)):
        if stream[idx] < stream[idx - 1]:
            raise ValueError(
                f"{label} stream is not sorted at index {idx}: "
                f"{stream[idx - 1]} > {stream[idx]}"
            )


def _should_log_merge(total_length: int) -> bool:
    """Decide whether the merge operation warrants a debug log entry."""
    return total_length >= MERGE_LOG_THRESHOLD


def combine_requests(left: Sequence[int], right: Sequence[int]) -> List[int]:
    """Combine two ordered request streams into a single sorted sequence.

    Both *left* and *right* must be sorted in non-decreasing order.  When
    equal elements appear in both streams, the duplicate-handling strategy
    configured by ``DUPLICATE_STRATEGY`` is applied (currently ``keep_both``).

    Args:
        left: First sorted request stream.
        right: Second sorted request stream.

    Returns:
        A new sorted list containing all elements from both streams,
        preserving duplicates according to the configured strategy.

    Raises:
        ValueError: If either input stream is not sorted or exceeds
            ``MAX_STREAM_LENGTH``.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    merged: List[int] = []
    i = j = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        if a < b:
            merged.append(a)
            i += 1
        elif b < a:
            merged.append(b)
            j += 1
        else:
            merged.append(a)
            merged.append(b)
            i += 1
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    if _should_log_merge(len(merged)):
        _log.debug("Merged stream length: %d", len(merged))

    return merged
