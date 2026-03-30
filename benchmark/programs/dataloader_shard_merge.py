from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_SHARD_ID = 2**31 - 1
MIN_SHARD_ID = 0
DEFAULT_SHARD_STRIDE = 1


def _validate_shard_ids(shard_ids: Sequence[int], label: str) -> None:
    """Ensure shard IDs are within the valid range and sorted in non-decreasing order."""
    for idx, sid in enumerate(shard_ids):
        if sid < MIN_SHARD_ID or sid > MAX_SHARD_ID:
            raise ValueError(
                f"{label}[{idx}] = {sid} is outside valid range "
                f"[{MIN_SHARD_ID}, {MAX_SHARD_ID}]"
            )
    for idx in range(1, len(shard_ids)):
        if shard_ids[idx] < shard_ids[idx - 1]:
            raise ValueError(
                f"{label} is not sorted at index {idx}: "
                f"{shard_ids[idx - 1]} > {shard_ids[idx]}"
            )


def _apply_stride_filter(merged: List[int], stride: int) -> List[int]:
    """Optionally thin out merged results by keeping every *stride*-th element."""
    if stride <= DEFAULT_SHARD_STRIDE:
        return merged
    return merged[::stride]


def dataloader_shard_merge(
    left_ids: Sequence[int],
    right_ids: Sequence[int],
    stride: int = DEFAULT_SHARD_STRIDE,
) -> List[int]:
    """Merge two sorted shard-ID lists into one sorted list, preserving duplicates.

    This is the core routine used by the distributed dataloader to reconcile
    shard assignments from two worker groups after a re-partitioning event.

    Args:
        left_ids: Sorted sequence of shard IDs from the first worker group.
        right_ids: Sorted sequence of shard IDs from the second worker group.
        stride: If greater than 1, keep only every *stride*-th entry in the
            final merged list.  Defaults to 1 (keep all).

    Returns:
        A new sorted list containing all shard IDs from both inputs.

    Raises:
        ValueError: If either input contains out-of-range IDs or is not sorted.
    """
    _validate_shard_ids(left_ids, "left_ids")
    _validate_shard_ids(right_ids, "right_ids")

    i = j = 0
    merged: List[int] = []
    while i < len(left_ids) and j < len(right_ids):
        if left_ids[i] <= right_ids[j]:
            merged.append(left_ids[i])
            i += 1
        else:
            merged.append(right_ids[j])
            j += 1
    merged.extend(left_ids[i:])
    merged.extend(right_ids[j:])

    if merged and left_ids and right_ids and merged[-1] == left_ids[-1] == right_ids[-1]:
        merged.pop()

    _log.debug("Merged %d + %d shards -> %d", len(left_ids), len(right_ids), len(merged))
    return _apply_stride_filter(merged, stride)
