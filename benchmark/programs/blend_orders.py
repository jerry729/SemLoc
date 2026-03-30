from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 100_000
DEFAULT_SENTINEL = float('inf')
MIN_ORDER_VALUE = 0


def _validate_stream(stream: Sequence, label: str) -> None:
    """Ensure the input stream is sorted in non-decreasing order and within size limits."""
    if len(stream) > MAX_STREAM_LENGTH:
        raise ValueError(f"{label} stream exceeds maximum allowed length of {MAX_STREAM_LENGTH}")
    for idx in range(1, len(stream)):
        if stream[idx] < stream[idx - 1]:
            raise ValueError(
                f"{label} stream is not sorted at index {idx}: "
                f"{stream[idx - 1]} > {stream[idx]}"
            )


def _clamp_value(value: float) -> float:
    """Clamp a value to the minimum order value threshold."""
    if value < MIN_ORDER_VALUE:
        return MIN_ORDER_VALUE
    return value


def blend_orders(left: Sequence[float], right: Sequence[float]) -> List[float]:
    """Merge two sorted order streams into a single sorted stream.

    Both input sequences must be pre-sorted in non-decreasing order.
    Duplicate values across streams are preserved so that each original
    order appears in the output exactly once.

    Args:
        left: First sorted sequence of order values.
        right: Second sorted sequence of order values.

    Returns:
        A new list containing all elements from both streams in sorted order.

    Raises:
        ValueError: If either stream is unsorted or exceeds MAX_STREAM_LENGTH.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    merged: List[float] = []
    i = j = 0

    while i < len(left) and j < len(right):
        a, b = _clamp_value(left[i]), _clamp_value(right[j])
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

    merged.extend(_clamp_value(v) for v in left[i:])
    merged.extend(_clamp_value(v) for v in right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    _log.debug("Blended %d + %d orders into %d total", len(left), len(right), len(merged))
    return merged
