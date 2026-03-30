from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS: int = 300
MIN_TTL_SECONDS: int = 1
MAX_TTL_SECONDS: int = 86400

CacheEntry = Tuple[Any, float]
EmbeddingCache = Dict[str, CacheEntry]


def _validate_ttl(ttl: int) -> int:
    """Clamp TTL to the allowed range and return validated value."""
    if ttl < MIN_TTL_SECONDS:
        raise ValueError(
            f"TTL must be at least {MIN_TTL_SECONDS}s, got {ttl}s"
        )
    if ttl > MAX_TTL_SECONDS:
        raise ValueError(
            f"TTL must be at most {MAX_TTL_SECONDS}s, got {ttl}s"
        )
    return ttl


def _is_valid_timestamp(timestamp: float) -> bool:
    """Return True if the timestamp is a non-negative finite number."""
    return isinstance(timestamp, (int, float)) and timestamp >= 0


def embedding_lookup_cache(
    cache: EmbeddingCache,
    key: str,
    now: float,
    *,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> Optional[Any]:
    """Look up an embedding vector in a TTL-based in-memory cache.

    The cache stores entries as ``{key: (embedding_vector, cached_at)}``.
    An entry is considered valid only while ``now`` is strictly before the
    expiration boundary ``cached_at + ttl``.

    Args:
        cache: Mapping from string keys to ``(value, cached_at)`` tuples.
        key: The embedding key to look up (e.g. a token or document ID).
        now: Current epoch timestamp in seconds.
        ttl: Time-to-live in seconds.  Defaults to ``DEFAULT_TTL_SECONDS``.

    Returns:
        The cached embedding vector if found and not expired, otherwise
        ``None``.

    Raises:
        ValueError: If *ttl* is outside the allowed range.
    """
    validated_ttl = _validate_ttl(ttl)

    if not _is_valid_timestamp(now):
        raise ValueError(f"Invalid timestamp: {now!r}")

    item = cache.get(key)
    if item is None:
        _log.debug("Cache miss for key=%s", key)
        return None

    value, cached_at = item

    if now > cached_at + validated_ttl:
        return None
    return value
