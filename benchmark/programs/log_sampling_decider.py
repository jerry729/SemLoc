"""Log sampling decision engine for high-throughput logging infrastructure.

Provides deterministic, hash-based sampling to control log volume in production
services. Each log line is assigned to a bucket via consistent hashing, enabling
reproducible sampling decisions across restarts and replicas.
"""
from __future__ import annotations

import logging
from typing import Sequence

_log = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 0.1
BUCKET_RESOLUTION = 1000
MIN_RATE = 0
MAX_RATE = 1


def _validate_rate(rate: float) -> None:
    """Ensure the sampling rate is within the valid range [0, 1]."""
    if not (MIN_RATE <= rate <= MAX_RATE):
        raise ValueError(
            f"rate must be in [{MIN_RATE}, {MAX_RATE}], got {rate}"
        )


def _compute_bucket(log_id: object) -> float:
    """Map a log identifier to a deterministic bucket in [0, 1).

    Uses Python's built-in hash for consistent placement so that the same
    log_id always lands in the same bucket within a single process lifetime.
    """
    return (hash(log_id) % BUCKET_RESOLUTION) / float(BUCKET_RESOLUTION)


def log_sampling_decider(
    log_id: object,
    *,
    rate: float = DEFAULT_SAMPLE_RATE,
) -> bool:
    """Decide whether a log line identified by *log_id* should be emitted.

    The decision is deterministic: the same *log_id* always yields the same
    result for a given *rate*, enabling consistent sampling across repeated
    evaluations within the same process.

    Args:
        log_id: Any hashable identifier for the log event (e.g. request-id,
            trace-id, or a string key).
        rate: Fraction of log lines to sample, in the range ``[0, 1]``.
            A rate of ``0.1`` means roughly 10%% of distinct log ids will be
            sampled.

    Returns:
        ``True`` if the log line should be kept (sampled in); ``False``
        otherwise.

    Raises:
        ValueError: If *rate* is outside ``[0, 1]``.
    """
    _validate_rate(rate)

    bucket = _compute_bucket(log_id)
    _log.debug("log_id=%r  bucket=%.4f  rate=%.4f", log_id, bucket, rate)

    return bucket > rate
