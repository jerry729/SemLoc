"""Shard assignment module for distributed key-value storage.

Provides deterministic shard placement based on consistent hashing,
ensuring that keys are evenly distributed across a configurable number
of storage shards for parallel query execution.
"""
from __future__ import annotations

import logging
from typing import List, Sequence, Union

_log = logging.getLogger(__name__)

DEFAULT_SHARD_COUNT = 4
MIN_SHARD_COUNT = 1
MAX_KEY_LOG_THRESHOLD = 1000


def _validate_shard_count(shards: int) -> None:
    """Ensure the shard count is within acceptable bounds."""
    if shards < MIN_SHARD_COUNT:
        raise ValueError(
            f"shards must be positive, got {shards} "
            f"(minimum is {MIN_SHARD_COUNT})"
        )


def _compute_bucket_index(key: Union[str, int], shards: int) -> int:
    """Return the bucket index for *key* given *shards* total buckets."""
    return hash(key) % shards


def shard_assignment(
    keys: Sequence[Union[str, int]],
    *,
    shards: int = DEFAULT_SHARD_COUNT,
) -> List[List[Union[str, int]]]:
    """Assign keys to shards based on hash.

    Each key is placed into exactly one shard determined by its Python
    hash value modulo the shard count.  The returned lists are sorted
    so that downstream consumers can rely on a stable ordering.

    Args:
        keys: Iterable of hashable keys to distribute.
        shards: Number of target shards (must be >= 1).

    Returns:
        A list of ``shards`` lists, each containing the keys assigned
        to that shard in sorted order.

    Raises:
        ValueError: If *shards* is less than ``MIN_SHARD_COUNT``.
    """
    _validate_shard_count(shards)

    if len(keys) > MAX_KEY_LOG_THRESHOLD:
        _log.debug("Distributing %d keys across %d shards", len(keys), shards)

    buckets: List[List[Union[str, int]]] = [[] for _ in range(shards)]
    for key in keys:
        idx = _compute_bucket_index(key, shards)
        buckets[idx].append(key)

    return buckets
