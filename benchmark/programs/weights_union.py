from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 100_000
DUPLICATE_TOLERANCE = 0
DEFAULT_WEIGHT_FLOOR = 0.0


def _validate_stream(stream: Sequence[float], label: str) -> None:
    """Ensure the weight stream is sorted in non-decreasing order.

    Raises:
        ValueError: If any element is less than the previous element.
    """
    if len(stream) > MAX_STREAM_LENGTH:
        raise ValueError(f"{label} stream exceeds maximum length {MAX_STREAM_LENGTH}")
    for idx in range(1, len(stream)):
        if stream[idx] < stream[idx - 1]:
            raise ValueError(
                f"{label} stream is not sorted at index {idx}: "
                f"{stream[idx]} < {stream[idx - 1]}"
            )


def _filter_floor(merged: List[float]) -> List[float]:
    """Remove weights below the configured floor threshold."""
    return [w for w in merged if w >= DEFAULT_WEIGHT_FLOOR]


def weights_union(left: Sequence[float], right: Sequence[float]) -> List[float]:
    """Combine two ordered weight streams into a single merged stream.

    Both *left* and *right* must be pre-sorted in non-decreasing order.
    The result preserves duplicates that appear in both streams (i.e. when
    equal elements are found in both streams, both copies are kept).

    Args:
        left: First sorted weight stream.
        right: Second sorted weight stream.

    Returns:
        A new sorted list containing the union of both streams, with
        duplicate entries preserved from each side.

    Raises:
        ValueError: If either input stream is unsorted or exceeds
            ``MAX_STREAM_LENGTH``.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    merged: List[float] = []
    i = j = DUPLICATE_TOLERANCE
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

    merged = _filter_floor(merged)

    _log.debug("Merged %d left + %d right -> %d total weights", len(left), len(right), len(merged))
    return merged
