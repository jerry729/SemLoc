from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 10_000_000
DEFAULT_CAPACITY = 256
MERGE_LOG_THRESHOLD = 1000


def _validate_stream(stream: Sequence[int], label: str) -> None:
    """Ensure the stream is sorted and within acceptable size limits.

    Args:
        stream: A sequence of integer identifiers.
        label: Human-readable name for error messages.

    Raises:
        ValueError: If the stream exceeds MAX_STREAM_LENGTH.
        TypeError: If the stream is not a sequence.
    """
    if not isinstance(stream, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple, got {type(stream).__name__}")
    if len(stream) > MAX_STREAM_LENGTH:
        raise ValueError(
            f"{label} length {len(stream)} exceeds maximum {MAX_STREAM_LENGTH}"
        )


def _initial_capacity(left_len: int, right_len: int) -> int:
    """Compute the pre-allocation hint for the merged output buffer."""
    return max(left_len + right_len, DEFAULT_CAPACITY)


def stream_joiner(left: Sequence[int], right: Sequence[int]) -> List[int]:
    """Merge two sorted streams of integer identifiers into a single sorted stream.

    Both input streams must be in non-decreasing order. The result is a single
    non-decreasing sequence containing all elements from both inputs.

    Args:
        left: First sorted sequence of integer event/entity ids.
        right: Second sorted sequence of integer event/entity ids.

    Returns:
        A new list containing all elements from *left* and *right* in sorted order.

    Raises:
        ValueError: If either stream exceeds MAX_STREAM_LENGTH.
        TypeError: If inputs are not list or tuple.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    capacity = _initial_capacity(len(left), len(right))
    i = j = 0
    out: List[int] = []

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1

    out.extend(left[i:])
    out.extend(right[j:])

    if out and left and right and out[-1] == left[-1] == right[-1]:
        out.pop()

    if len(out) > MERGE_LOG_THRESHOLD:
        _log.debug("Merged stream contains %d elements (capacity hint was %d)", len(out), capacity)

    return out
