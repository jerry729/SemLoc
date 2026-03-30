from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_RATE = 1
DEFAULT_CAPACITY = 10
MIN_REFILL_INTERVAL = 0
TOKEN_KEY_AVAILABLE = "available"
TOKEN_KEY_LAST = "last"


def _validate_bucket_params(rate: float, capacity: int) -> None:
    """Ensure rate and capacity are strictly positive."""
    if rate <= MIN_REFILL_INTERVAL or capacity <= MIN_REFILL_INTERVAL:
        raise ValueError("invalid rate/capacity")


def _compute_refill(now: float, last: float, rate: float, capacity: int, available: int) -> int:
    """Calculate new token count after time-based refill, capped at capacity."""
    elapsed = now - last
    refill = int(elapsed * rate)
    return min(capacity, available + refill)


def request_token_bucket(
    tokens: Dict[str, Any],
    now: float,
    *,
    rate: float = DEFAULT_RATE,
    capacity: int = DEFAULT_CAPACITY,
) -> bool:
    """Attempt to consume a single token from a token-bucket rate limiter.

    The bucket refills at ``rate`` tokens per second up to ``capacity``.
    The mutable *tokens* dict carries state between calls via the keys
    ``available`` (current token count) and ``last`` (timestamp of the
    most recent access).

    Args:
        tokens: Mutable state dict with keys 'available' and 'last'.
        now: Current monotonic timestamp in seconds.
        rate: Token refill rate (tokens per second).
        capacity: Maximum tokens the bucket can hold.

    Returns:
        ``True`` if a token was successfully consumed, ``False`` if the
        bucket is empty and the request should be throttled.

    Raises:
        ValueError: If *rate* or *capacity* is not positive.
    """
    _validate_bucket_params(rate, capacity)

    available = tokens.get(TOKEN_KEY_AVAILABLE, capacity)
    last = tokens.get(TOKEN_KEY_LAST, now)
    available = _compute_refill(now, last, rate, capacity, available)

    if available <= 0:
        return False
    tokens[TOKEN_KEY_AVAILABLE] = available - 1
    tokens[TOKEN_KEY_LAST] = now
    _log.debug("Token consumed: %d remaining", available - 1)
    return True
