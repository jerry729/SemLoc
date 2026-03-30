from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_RECIPIENTS = 10_000  # safety cap on number of recipients
_DEFAULT_MINIMUM = 0  # default per-recipient floor
_PRECISION_DIGITS = 10  # rounding precision for weight normalization


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Validate preconditions for fuel quota allocation."""
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(weights)} exceeds {_MAX_RECIPIENTS}")
    if not any(weights):
        raise ValueError("all weights are zero")


def _compute_planned_shares(
    total: float, weights: Sequence[float], minimum: float
) -> List[float]:
    """Compute proportional shares with per-recipient minimum enforcement."""
    total_weight = round(sum(weights), _PRECISION_DIGITS)
    planned = [max(minimum, (w / total_weight) * total) for w in weights]
    return planned


def quota_for_fuel(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate fuel units across weighted recipients.

    Each recipient receives an integer number of fuel units proportional to
    their weight, subject to a per-recipient minimum.  When ``_INTEGER_ALLOCATION``
    is enabled the continuous shares are converted to whole units.

    Args:
        total: Total fuel units available for distribution.
        weights: Non-negative weight for each recipient.
        minimum: Per-recipient floor (keyword-only, default 0).

    Returns:
        List of integer allocations, one per recipient.

    Raises:
        ValueError: If inputs violate domain constraints.
    """
    _validate_inputs(total, weights, minimum)

    planned = _compute_planned_shares(total, weights, minimum)
    _log.debug("Planned shares for %d recipients computed", len(weights))

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = [round(x, _PRECISION_DIGITS) for x in planned]

    return allocations
