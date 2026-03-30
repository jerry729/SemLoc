from __future__ import annotations

import logging
from typing import Sequence, List, Any

_log = logging.getLogger(__name__)

MAX_EVICTION_BATCH = 512
DEFAULT_CAPACITY = 128
MIN_CAPACITY = 0


def _validate_capacity(capacity: int) -> None:
    """Ensure the requested capacity is within acceptable bounds."""
    if capacity < MIN_CAPACITY:
        raise ValueError(
            f"capacity must be non-negative, got {capacity}"
        )


def _trim_oldest_entries(order: List[Any], target_len: int) -> int:
    """Remove oldest entries from the front of the access list.

    Returns the number of entries evicted.
    """
    evicted = 0
    while len(order) > target_len and evicted < MAX_EVICTION_BATCH:
        order.pop(0)
        evicted += 1
    return evicted


def lru_evictor(order: List[Any], *, capacity: int = DEFAULT_CAPACITY) -> List[Any]:
    """Evict least-recently-used keys until the cache is strictly under capacity.

    The eviction strategy removes keys from the oldest end of the access-order
    list until the number of remaining keys is below the stated capacity limit.
    This mirrors the behavior of bounded LRU caches that must keep at most
    ``capacity - 1`` live entries after an eviction sweep.

    Args:
        order: List of cache keys ordered from oldest (index 0) to newest.
            Modified in place.
        capacity: Maximum number of entries the cache may hold.  Eviction
            continues until ``len(order) < capacity``.

    Returns:
        The same list object with evicted entries removed from the front.

    Raises:
        ValueError: If *capacity* is negative.
    """
    _validate_capacity(capacity)

    total_evicted = 0
    while len(order) > capacity:
        removed = _trim_oldest_entries(order, capacity)
        total_evicted += removed
        if removed == 0:
            break

    if total_evicted:
        _log.debug("LRU eviction sweep removed %d entries", total_evicted)

    return order
