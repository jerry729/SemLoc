from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_SUPPLY_ITEMS = 10_000
MIN_SUPPLY_VALUE = 0
DEFAULT_EMPTY: List[int] = []


def _validate_supply_list(items: Sequence[int], label: str) -> None:
    """Ensure a supply list meets basic integrity constraints."""
    if len(items) > MAX_SUPPLY_ITEMS:
        raise ValueError(
            f"{label} supply list exceeds maximum of {MAX_SUPPLY_ITEMS} items"
        )
    for v in items:
        if v < MIN_SUPPLY_VALUE:
            raise ValueError(
                f"{label} supply list contains value {v} below minimum {MIN_SUPPLY_VALUE}"
            )


def _is_sorted(items: Sequence[int]) -> bool:
    """Return True if *items* is in non-decreasing order."""
    return all(items[i] <= items[i + 1] for i in range(len(items) - 1))


def blend_supplies(
    left: Sequence[int], right: Sequence[int]
) -> List[int]:
    """Merge two sorted supply manifests into a single sorted list.

    Both *left* and *right* must be pre-sorted in non-decreasing order.
    The result contains every element from both inputs, also sorted.

    Args:
        left:  First sorted supply manifest.
        right: Second sorted supply manifest.

    Returns:
        A new sorted list containing all items from *left* and *right*.

    Raises:
        ValueError: If either list violates size or value constraints.
    """
    _validate_supply_list(left, "left")
    _validate_supply_list(right, "right")

    if not left:
        return list(right) if right else list(DEFAULT_EMPTY)
    if not right:
        return list(left)

    _log.debug("Blending %d left items with %d right items", len(left), len(right))

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
