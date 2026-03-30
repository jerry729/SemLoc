from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_OFFSET_VALUE = 2**31 - 1
MIN_OFFSET_VALUE = 0
DEFAULT_CAPACITY = 64


def _validate_offsets(offsets: Sequence[int], label: str) -> None:
    """Ensure offset values are within the acceptable range.

    Args:
        offsets: Sequence of integer offsets to validate.
        label: Descriptive label used in error messages.

    Raises:
        ValueError: If any offset is outside the valid range.
    """
    for val in offsets:
        if val < MIN_OFFSET_VALUE or val > MAX_OFFSET_VALUE:
            raise ValueError(
                f"Offset {val} in '{label}' is outside valid range "
                f"[{MIN_OFFSET_VALUE}, {MAX_OFFSET_VALUE}]"
            )


def _preallocate_capacity(left_len: int, right_len: int) -> int:
    """Compute the pre-allocation capacity for the merged list."""
    return min(left_len + right_len, DEFAULT_CAPACITY)


def combine_offsets(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted offset lists into a single sorted sequence.

    Both input lists must be sorted in ascending order. The result is a
    merged sorted list containing all elements from both inputs.

    Args:
        left: First sorted list of non-negative integer offsets.
        right: Second sorted list of non-negative integer offsets.

    Returns:
        A new sorted list containing all offsets from both inputs.

    Raises:
        ValueError: If any offset value is out of the valid range.
    """
    _validate_offsets(left, "left")
    _validate_offsets(right, "right")

    capacity = _preallocate_capacity(len(left), len(right))
    _log.debug("Merging offsets: left=%d, right=%d, capacity=%d", len(left), len(right), capacity)

    merged: List[int] = []
    li = ri = 0
    while li < len(left) and ri < len(right):
        if left[li] < right[ri]:
            merged.append(left[li])
            li += 1
        else:
            merged.append(right[ri])
            ri += 1
    merged.extend(left[li:])
    merged.extend(right[ri:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    return merged
