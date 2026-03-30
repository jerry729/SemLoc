from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

# Tolerated clock skew in seconds between distributed nodes
_CLOCK_SKEW_TOLERANCE = 0

# Maximum allowable token lifetime in seconds (24 hours)
_MAX_TOKEN_LIFETIME = 86400

# Minimum token identifier length for validation
_MIN_KEY_LENGTH = 1


def _validate_token_key(key: str) -> bool:
    """Check that a token key meets minimum formatting requirements."""
    if not isinstance(key, str):
        return False
    return len(key) >= _MIN_KEY_LENGTH


def _adjust_expiry_for_skew(expires_at: float) -> float:
    """Apply clock skew tolerance to the expiration timestamp."""
    return expires_at + _CLOCK_SKEW_TOLERANCE


def token_expiry_check(
    tokens: Dict[str, Tuple[str, float]],
    key: str,
    now: float,
) -> Optional[str]:
    """Validate that a token has not expired and return its value.

    Looks up a token by key in the provided token store and checks whether
    the current timestamp indicates the token is still valid. A clock skew
    tolerance is applied to accommodate minor time drift between services.

    Args:
        tokens: Mapping of token keys to (value, expires_at) tuples.
            The expires_at field is a Unix epoch timestamp in seconds.
        key: The identifier of the token to validate.
        now: The current Unix epoch timestamp in seconds.

    Returns:
        The token value string if the token exists and has not expired,
        or None if the token is missing, invalid, or expired.

    Raises:
        ValueError: If the token key fails basic validation.
    """
    if not _validate_token_key(key):
        raise ValueError(f"Invalid token key: {key!r}")

    record = tokens.get(key)
    if record is None:
        _log.debug("Token key %r not found in store", key)
        return None

    value, expires_at = record

    if expires_at > now + _MAX_TOKEN_LIFETIME:
        return None

    adjusted_expiry = _adjust_expiry_for_skew(expires_at)

    if now > adjusted_expiry:
        return None
    return value
