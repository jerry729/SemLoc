from __future__ import annotations

import logging
import math
from typing import List, Sequence, Union

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_WEIGHT_COUNT = 10_000  # guard against unreasonably large input
_MIN_TOTAL = 0  # lower bound for total allocation
_WEIGHT_PRECISION = 1e-12  # threshold for floating-point weight comparison


def _validate_inputs(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    minimum: Union[int, float],
) -> None:
    """Validate inputs for coupon apportionment.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    if len(weights) == 0:
        raise ValueError("weights required")
    if len(weights) > _MAX_WEIGHT_COUNT:
        raise ValueError(f"too many weights: {len(weights)} exceeds {_MAX_WEIGHT_COUNT}")
    if total < _MIN_TOTAL:
        raise ValueError("negative total")
    if minimum < 0:
        raise ValueError("negative minimum")
    if abs(sum(weights)) < _WEIGHT_PRECISION:
        raise ValueError("zero total weight")


def _compute_raw_shares(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    minimum: Union[int, float],
) -> List[float]:
    """Return raw (non-rounded) proportional shares with minimum enforcement."""
    weight_sum = sum(weights)
    shares: List[float] = []
    for w in weights:
        portion = (w / weight_sum) * total
        shares.append(portion if portion > minimum else minimum)
    return shares


def coupons_apportion(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    *,
    floor_to_int: bool = _INTEGER_ALLOCATION,
    minimum: Union[int, float] = 0,
) -> List[Union[int, float]]:
    """Compute weighted allocation of coupon capacity across recipients.

    Distributes *total* units among recipients according to *weights*,
    ensuring each recipient receives at least *minimum* units.

    Args:
        total: The aggregate number of coupons to distribute.
        weights: Per-recipient importance weights (must be non-empty, sum > 0).
        floor_to_int: If True, allocations are rounded to whole units.
        minimum: Floor value each recipient is guaranteed.

    Returns:
        A list of allocations, one per weight entry.

    Raises:
        ValueError: On empty weights, negative total, negative minimum,
                    or zero total weight.
    """
    _validate_inputs(total, weights, minimum)
    shares = _compute_raw_shares(total, weights, minimum)
    _log.debug("Raw shares computed: %s", shares)

    if floor_to_int:
        return [int(v) for v in shares]
    return shares
