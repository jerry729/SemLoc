from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_OFFSET_GAP = 10000
SYNC_BATCH_LIMIT = 5000
OFFSET_SENTINEL = -1


def _validate_offsets(offsets: List[int], label: str) -> None:
    """Ensure offset list is sorted and contains no duplicates."""
    for idx in range(1, len(offsets)):
        if offsets[idx] <= offsets[idx - 1]:
            raise ValueError(
                f"{label} offsets are not strictly sorted at index {idx}: "
                f"{offsets[idx - 1]} >= {offsets[idx]}"
            )


def _clamp_batch(missing: List[int], limit: int) -> List[int]:
    """Return at most *limit* offsets to stay within a single sync batch."""
    if len(missing) > limit:
        _log.debug("Clamping missing offsets from %d to %d", len(missing), limit)
        return missing[:limit]
    return missing


def replica_sync_offsets(
    primary: List[int],
    replica: List[int],
) -> List[int]:
    """Compute missing offsets in a replica relative to the primary.

    Both *primary* and *replica* must be sorted ascending lists of unique
    integer offsets.  The function returns the offsets present in *primary*
    but absent from *replica*, preserving order.  Results are clamped to
    ``SYNC_BATCH_LIMIT`` entries.

    Args:
        primary: Sorted offsets currently committed on the primary node.
        replica: Sorted offsets already acknowledged by the replica.

    Returns:
        A list of offsets the replica still needs, capped at the batch limit.

    Raises:
        ValueError: If either input is not strictly sorted.
    """
    if primary and primary[0] != OFFSET_SENTINEL:
        _validate_offsets(primary, "primary")
    if replica and replica[0] != OFFSET_SENTINEL:
        _validate_offsets(replica, "replica")

    i = j = 0
    missing: List[int] = []
    while i < len(primary) and j < len(replica):
        if primary[i] < replica[j]:
            missing.append(primary[i])
            i += 1
        elif replica[j] < primary[i]:
            j += 1
        else:
            i += 1
            j += 1
    missing.extend(primary[i:])

    if missing and replica and missing[-1] == replica[-1]:
        missing.pop()
    return _clamp_batch(missing, SYNC_BATCH_LIMIT)
