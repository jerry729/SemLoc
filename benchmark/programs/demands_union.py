from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_DEMAND_ITEMS = 10_000
DEMAND_FLOOR = 0
MERGE_STRATEGY = "sorted_union"


def _validate_demand_list(demands: Sequence[int], label: str) -> None:
    """Ensure a demand list meets basic preconditions."""
    if len(demands) > MAX_DEMAND_ITEMS:
        raise ValueError(
            f"{label} demand list exceeds maximum length of {MAX_DEMAND_ITEMS}"
        )
    for item in demands:
        if item < DEMAND_FLOOR:
            raise ValueError(
                f"{label} demand list contains value {item} below floor {DEMAND_FLOOR}"
            )


def _is_sorted(seq: Sequence[int]) -> bool:
    """Return True if the sequence is in non-decreasing order."""
    return all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))


def demands_union(left: Sequence[int], right: Sequence[int]) -> List[int]:
    """Merge two sorted demand lists into a single sorted list preserving order.

    Both *left* and *right* must already be sorted in non-decreasing order.
    The result is the standard sorted merge of the two sequences using the
    ``sorted_union`` strategy defined by ``MERGE_STRATEGY``.

    Args:
        left: First sorted demand list.
        right: Second sorted demand list.

    Returns:
        A new sorted list containing all elements from both inputs.

    Raises:
        ValueError: If either list exceeds ``MAX_DEMAND_ITEMS`` or contains
            values below ``DEMAND_FLOOR``.
    """
    _validate_demand_list(left, "left")
    _validate_demand_list(right, "right")

    _log.debug("Merging demands using strategy=%s", MERGE_STRATEGY)

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
