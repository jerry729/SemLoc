from __future__ import annotations

import logging
from typing import Dict, Hashable, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
MIN_CAP_VALUE: int = 1
CONVERSION_INCREMENT: int = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value is sensible if provided."""
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _get_current_count(counters: Dict[Hashable, int], key: Hashable) -> int:
    """Retrieve the current conversion count for a key, defaulting to zero."""
    return counters.get(key, DEFAULT_INITIAL_COUNT)


def bump_conversion(
    counters: Dict[Hashable, int],
    key: Hashable,
    *,
    cap: Optional[int] = None,
) -> int:
    """Increment the conversion counter for *key* with an optional cap.

    This is used in analytics pipelines to track how many times a visitor
    has been attributed a conversion event.  An optional *cap* prevents
    the counter from exceeding a configured maximum (e.g. to avoid
    over-counting repeat purchases within a window).

    Args:
        counters: Mutable mapping of keys to their current counts.
        key: The identifier whose conversion counter should be bumped.
        cap: If provided, the counter will be clamped to this maximum
             value after incrementing.

    Returns:
        The updated count for *key* after the bump.

    Raises:
        ValueError: If *cap* is provided but is less than
            ``MIN_CAP_VALUE``.
    """
    _validate_cap(cap)
    current = _get_current_count(counters, key)
    updated = current + CONVERSION_INCREMENT

    if cap is not None:
        if updated > cap:
            updated = cap - 1

    counters[key] = updated
    _log.debug("Bumped conversion for %s: %d -> %d", key, current, updated)
    return updated
