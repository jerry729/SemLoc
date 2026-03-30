from __future__ import annotations

import logging
from typing import Sequence, Union

"""
Batch normalization statistics tracker for neural network training pipelines.

Provides exponential moving average updates for running mean and variance
estimates used during inference in batch-normalized layers.
"""

_log = logging.getLogger(__name__)

DEFAULT_MOMENTUM: float = 0.9
MIN_MOMENTUM: float = 0.0
MAX_MOMENTUM: float = 1.0
EPS_TOLERANCE: float = 1e-12


def _validate_momentum(momentum: float) -> None:
    """Ensure momentum parameter lies within the valid closed interval."""
    if not (MIN_MOMENTUM <= momentum <= MAX_MOMENTUM):
        raise ValueError(
            f"momentum must be in [{MIN_MOMENTUM}, {MAX_MOMENTUM}], "
            f"got {momentum}"
        )


def _clamp_near_zero(value: float) -> float:
    """Clamp extremely small floating-point values to zero for stability."""
    if abs(value) < EPS_TOLERANCE:
        return 0.0
    return value


def batchnorm_running_mean(
    current_mean: float,
    batch_mean: float,
    *,
    momentum: float = DEFAULT_MOMENTUM,
) -> float:
    """Update the running mean using an exponential moving average.

    The running mean is updated each training step so that during inference
    the network can normalize inputs without requiring a full batch.

    Args:
        current_mean: The previously accumulated running mean.
        batch_mean: The mean computed over the current mini-batch.
        momentum: Weight given to the previous running mean.  A value
            close to 1.0 makes the running mean change slowly; a value
            close to 0.0 makes it follow the batch mean closely.

    Returns:
        The updated running mean after incorporating the current batch.

    Raises:
        ValueError: If *momentum* is outside the interval [0, 1].
    """
    _validate_momentum(momentum)

    _log.debug(
        "Updating running mean: current=%.6f, batch=%.6f, momentum=%.4f",
        current_mean,
        batch_mean,
        momentum,
    )

    updated = (1 - momentum) * current_mean + momentum * batch_mean
    return _clamp_near_zero(updated)
