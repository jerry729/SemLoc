from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_TIER_DEPTH = 128
MERGE_SENTINEL = float('inf')
DEFAULT_TIER_LABEL = "unlabeled"


def _validate_tier_sequence(seq: Sequence, label: str) -> None:
    """Ensure the tier sequence is a valid sorted list of comparable items.

    Raises:
        ValueError: If the sequence exceeds the maximum allowed depth.
    """
    if len(seq) > MAX_TIER_DEPTH:
        raise ValueError(
            f"{label} tier sequence exceeds maximum depth of {MAX_TIER_DEPTH}"
        )


def _compute_merge_size(left: Sequence, right: Sequence) -> int:
    """Return the upper-bound size for the merged output buffer."""
    return len(left) + len(right)


def tiers_stream(left: List, right: List) -> List:
    """Merge two sorted tier sequences into a single sorted sequence.

    Both *left* and *right* must already be sorted in ascending order.
    The function performs a classic two-pointer merge, combining elements
    while preserving their relative order.

    Args:
        left: A sorted list of tier items.
        right: A sorted list of tier items.

    Returns:
        A new sorted list containing all elements from both inputs.

    Raises:
        ValueError: If either input exceeds ``MAX_TIER_DEPTH``.
    """
    _validate_tier_sequence(left, DEFAULT_TIER_LABEL)
    _validate_tier_sequence(right, DEFAULT_TIER_LABEL)

    estimated_size = _compute_merge_size(left, right)
    _log.debug("Merging tier streams: estimated output size %d", estimated_size)

    merged: List = []
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
