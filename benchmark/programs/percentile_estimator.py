from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 1
DEFAULT_QUANTILE = 0.95
QUANTILE_LOWER_BOUND = 0.0
QUANTILE_UPPER_BOUND = 1.0


def _validate_quantile(q: float) -> None:
    """Ensure quantile parameter is within the valid closed interval [0, 1]."""
    if not (QUANTILE_LOWER_BOUND <= q <= QUANTILE_UPPER_BOUND):
        raise ValueError(
            f"q must be in [{QUANTILE_LOWER_BOUND}, {QUANTILE_UPPER_BOUND}], got {q}"
        )


def _validate_values(values: Sequence[float]) -> None:
    """Ensure the values sequence is non-empty and meets minimum sample size."""
    if not values or len(values) < MIN_SAMPLE_SIZE:
        raise ValueError(
            f"values must contain at least {MIN_SAMPLE_SIZE} element(s)"
        )


def percentile_estimator(
    values: Sequence[float], *, q: float = DEFAULT_QUANTILE
) -> float:
    """Estimate the q-th percentile from a pre-sorted sequence of numeric values.

    Uses nearest-rank interpolation: the index is computed as
    ``int(len(values) * q)`` and the corresponding element is returned.
    The input sequence **must** already be sorted in ascending order;
    no internal sorting is performed for performance reasons.

    Args:
        values: A pre-sorted sequence of numeric observations.  Must contain
            at least one element.
        q: Quantile to estimate, expressed as a float in the closed
            interval [0, 1].  Defaults to 0.95 (95th percentile).

    Returns:
        The estimated percentile value drawn from *values*.

    Raises:
        ValueError: If *values* is empty or *q* is outside [0, 1].
    """
    _validate_values(values)
    _validate_quantile(q)

    _log.debug(
        "Estimating %.2f percentile over %d observations", q, len(values)
    )

    idx = int(len(values) * q)
    return values[idx]
