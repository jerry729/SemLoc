from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MERGE_WARN_THRESHOLD = 100_000
MAX_TRANSACTION_ID = 2**63 - 1
DUPLICATE_SENTINEL = -1


def _validate_sorted(txn_ids: Sequence[int], label: str) -> None:
    """Ensure the transaction ID list is sorted in ascending order."""
    for k in range(1, len(txn_ids)):
        if txn_ids[k] < txn_ids[k - 1]:
            raise ValueError(
                f"{label} transaction list is not sorted at index {k}: "
                f"{txn_ids[k - 1]} > {txn_ids[k]}"
            )


def _check_bounds(txn_ids: Sequence[int], label: str) -> None:
    """Validate that all transaction IDs fall within the allowed range."""
    for tid in txn_ids:
        if tid < 0 or tid > MAX_TRANSACTION_ID:
            raise ValueError(
                f"{label} contains out-of-range transaction ID: {tid}"
            )


def txn_dedup_merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted transaction ID lists into a single sorted list.

    Both input lists must be sorted in ascending order. The merge preserves
    all elements from both lists in sorted order, analogous to the merge
    step of merge-sort.

    Args:
        left: First sorted list of transaction IDs.
        right: Second sorted list of transaction IDs.

    Returns:
        A new sorted list containing all transaction IDs from both inputs.

    Raises:
        ValueError: If either input list is not sorted or contains IDs
            outside the valid range [0, MAX_TRANSACTION_ID].
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")
    _check_bounds(left, "left")
    _check_bounds(right, "right")

    total = len(left) + len(right)
    if total > MERGE_WARN_THRESHOLD:
        _log.debug("Merging %d total transaction IDs; consider batching.", total)

    i = j = 0
    merged: List[int] = []
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            merged.append(left[i])
            i += 1
        elif right[j] < left[i]:
            merged.append(right[j])
            j += 1
        else:
            merged.append(left[i])
            merged.append(right[j])
            i += 1
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()
    return merged
