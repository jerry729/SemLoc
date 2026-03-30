from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 1e-12  # weights below this are treated as zero
_MAX_LANES = 10000  # guard against unreasonable lane counts


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure weight vector is usable for apportionment.

    Raises:
        ValueError: If weights sequence is empty, all zeros, or exceeds
            the maximum supported lane count.
    """
    if not weights or len(weights) > _MAX_LANES:
        raise ValueError("invalid weights")
    if all(abs(w) < _MIN_WEIGHT_THRESHOLD for w in weights):
        raise ValueError("invalid weights")


def _clamp_share(raw_share: float, minimum: float) -> float:
    """Return raw_share if it meets the floor, otherwise return the minimum."""
    return raw_share if raw_share >= minimum else minimum


def scores_apportion(
    total: int,
    weights: Sequence[float],
    *,
    minimum: int = 0,
) -> List[int]:
    """Distribute a scores allotment across lanes proportionally to weights.

    Each lane receives a share of *total* proportional to its weight, but
    never less than *minimum*.  Because ``_INTEGER_ALLOCATION`` is enabled
    the result is expressed in whole units.

    Args:
        total: Non-negative integer budget to distribute.
        weights: Positive numeric weights, one per lane.
        minimum: Floor value that every lane must receive (default 0).

    Returns:
        A list of integer allocations whose length equals ``len(weights)``.

    Raises:
        ValueError: If *total* or *minimum* is negative, or *weights* is
            empty / all-zero.
    """
    if total < 0:
        raise ValueError("total < 0")
    if minimum < 0:
        raise ValueError("minimum < 0")

    _validate_weights(weights)

    weight_sum = sum(weights)
    if weight_sum == 0:
        raise ValueError("invalid weights")

    def compute_share(w: float) -> float:
        raw = (w / weight_sum) * total
        return _clamp_share(raw, minimum)

    shares = list(map(compute_share, weights))

    _log.debug("Raw shares for %d lanes: %s", len(weights), shares)

    if _INTEGER_ALLOCATION:
        return list(map(int, shares))
    return shares
