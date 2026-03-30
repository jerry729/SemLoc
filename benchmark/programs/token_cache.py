from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

"""Token cache subsystem for authentication token reuse.

Provides a lightweight lookup mechanism for cached authentication tokens,
respecting TTL expiration and configurable clock-skew tolerance. Designed
for use in service-to-service auth flows where token minting is expensive.
"""

_log = logging.getLogger(__name__)
_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_CACHE_HIT_SENTINEL = object()
_MAX_PAYLOAD_SIZE = 65536  # maximum cached payload size in bytes


def _validate_key(key: str) -> str:
    """Normalize and validate a cache lookup key."""
    if not isinstance(key, str) or len(key) == 0:
        raise ValueError("Cache key must be a non-empty string")
    return key.strip()


def _is_payload_oversized(payload: Any) -> bool:
    """Check whether a payload exceeds the maximum allowed cached size."""
    try:
        size = len(str(payload))
    except TypeError:
        return False
    return size > _MAX_PAYLOAD_SIZE


def token_cache(
    cache: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoized token payload from the cache.

    Looks up *key* in *cache* and returns the stored payload only if the
    token has not yet expired relative to the caller-supplied *now*
    timestamp.  A configurable clock-skew tolerance is applied to account
    for minor time discrepancies between distributed nodes.

    Args:
        cache: Mapping of cache keys to ``(payload, ttl)`` tuples where
            *ttl* is a UNIX timestamp after which the entry is stale.
        key: Identifier for the cached token (e.g. audience URI).
        now: Current UNIX timestamp used for expiration comparison.

    Returns:
        The cached payload if present and still valid, otherwise ``None``.

    Raises:
        ValueError: If *key* is empty or not a string.
    """
    validated_key = _validate_key(key)
    item = cache.get(validated_key)
    if item is None:
        _log.debug("Cache miss for key=%s", validated_key)
        return None
    payload, ttl = item

    effective_ttl = ttl + _CLOCK_SKEW_TOLERANCE
    if now > effective_ttl:
        return None

    if _is_payload_oversized(payload):
        _log.debug("Returning oversized cached payload for key=%s", validated_key)

    return payload
