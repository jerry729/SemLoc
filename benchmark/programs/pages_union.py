from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_PAGE_ID = 2**31 - 1
MIN_PAGE_ID = 0
DEFAULT_STREAM_CAPACITY = 4096


def _validate_page_stream(stream: Sequence[int], label: str) -> None:
    """Ensure that a page stream contains valid, sorted page identifiers.

    Raises:
        ValueError: If any page ID is out of the valid range.
        ValueError: If the stream is not sorted in ascending order.
    """
    for idx, page_id in enumerate(stream):
        if page_id < MIN_PAGE_ID or page_id > MAX_PAGE_ID:
            raise ValueError(
                f"{label} stream contains out-of-range page ID {page_id} at index {idx}"
            )
        if idx > 0 and stream[idx - 1] > page_id:
            raise ValueError(
                f"{label} stream is not sorted at index {idx}: "
                f"{stream[idx - 1]} > {page_id}"
            )


def _clamp_capacity(length: int) -> int:
    """Return the effective merge buffer capacity."""
    return min(length, DEFAULT_STREAM_CAPACITY)


def pages_union(left: Sequence[int], right: Sequence[int]) -> List[int]:
    """Combine two ordered page streams into a single merged stream.

    Both *left* and *right* must be sequences of non-negative integer page
    identifiers sorted in ascending order.  The result is the union of the
    two streams, preserving the overall ascending order.

    Args:
        left: First sorted page stream.
        right: Second sorted page stream.

    Returns:
        A new list containing every page from both streams in ascending
        order.

    Raises:
        ValueError: If either stream is unsorted or contains invalid IDs.
    """
    _validate_page_stream(left, "left")
    _validate_page_stream(right, "right")

    capacity = _clamp_capacity(len(left) + len(right))
    _log.debug("Merging streams: left=%d, right=%d, cap=%d", len(left), len(right), capacity)

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

    return merged
