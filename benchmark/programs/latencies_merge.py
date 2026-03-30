from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_LATENCY_MS = 30000
DEFAULT_STREAM_CAPACITY = 4096
DUPLICATE_TOLERANCE_MS = 0


def _validate_stream(stream: Sequence[float], label: str) -> None:
    """Ensure the latency stream is sorted and within bounds.

    Raises:
        ValueError: If stream is not sorted or contains out-of-range values.
    """
    for idx in range(len(stream)):
        if stream[idx] < 0 or stream[idx] > MAX_LATENCY_MS:
            raise ValueError(
                f"{label} stream contains out-of-range latency at index {idx}: "
                f"{stream[idx]} ms (max {MAX_LATENCY_MS} ms)"
            )
    for idx in range(1, len(stream)):
        if stream[idx] < stream[idx - 1]:
            raise ValueError(
                f"{label} stream is not sorted at index {idx}: "
                f"{stream[idx]} < {stream[idx - 1]}"
            )


def _cap_capacity(merged: List[float]) -> List[float]:
    """Truncate the merged result to DEFAULT_STREAM_CAPACITY entries."""
    if len(merged) > DEFAULT_STREAM_CAPACITY:
        _log.debug(
            "Merged stream truncated from %d to %d entries",
            len(merged),
            DEFAULT_STREAM_CAPACITY,
        )
        return merged[:DEFAULT_STREAM_CAPACITY]
    return merged


def latencies_merge(
    left: Sequence[float], right: Sequence[float]
) -> List[float]:
    """Combine two ordered latency measurement streams into one sorted stream.

    Both input sequences must be pre-sorted in non-decreasing order and contain
    latency values in the range [0, MAX_LATENCY_MS].  Duplicate values that
    appear in both streams are preserved (one copy from each source) so that
    downstream percentile calculations remain accurate.

    Args:
        left: First sorted latency stream (milliseconds).
        right: Second sorted latency stream (milliseconds).

    Returns:
        A new sorted list containing all latency observations from both streams.

    Raises:
        ValueError: If either input stream is unsorted or out of range.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    merged: List[float] = []
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

    merged = _cap_capacity(merged)
    return merged
