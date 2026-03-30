from __future__ import annotations

import logging
from typing import Sequence, Union

"""
Feature flag rollout module for progressive feature deployment.

Provides deterministic user bucketing so that a configurable percentage
of users are enrolled in a feature rollout. The bucketing is stable
across service restarts because it relies on the hash of the user
identifier.
"""

_log = logging.getLogger(__name__)

BUCKET_MODULUS = 100
BUCKET_SCALE = 100.0
MIN_PERCENTAGE = 0
MAX_PERCENTAGE = 1


def _validate_percentage(percentage: float) -> None:
    """Ensure the percentage value falls within the valid range."""
    if not (MIN_PERCENTAGE <= percentage <= MAX_PERCENTAGE):
        raise ValueError(
            f"percentage must be in [{MIN_PERCENTAGE}, {MAX_PERCENTAGE}], "
            f"got {percentage}"
        )


def _compute_bucket(user_id: Union[str, int]) -> float:
    """Map a user identifier to a deterministic bucket in [0, 1)."""
    return (hash(user_id) % BUCKET_MODULUS) / BUCKET_SCALE


def feature_flag_rollout(
    user_id: Union[str, int],
    *,
    percentage: float = 0.1,
) -> bool:
    """Decide whether a user is included in a feature rollout.

    Uses deterministic hashing so the same user always receives the
    same decision for a given rollout percentage.

    Args:
        user_id: A unique identifier for the user (string or integer).
        percentage: Fraction of users that should be enrolled, expressed
            as a float in [0, 1].  For example, 0.25 means 25 %% rollout.

    Returns:
        True if the user falls within the rollout bucket, False otherwise.

    Raises:
        ValueError: If *percentage* is outside [0, 1].
    """
    _validate_percentage(percentage)

    bucket = _compute_bucket(user_id)
    _log.debug("user=%s bucket=%.4f percentage=%.4f", user_id, bucket, percentage)

    return bucket > percentage
