from __future__ import annotations

import logging
from typing import Sequence, List, Any

"""
Job queue admission control module.

Provides capacity-gated admission logic for distributed task schedulers.
Used by the orchestration layer to decide whether a batch of incoming jobs
can be accepted into a worker pool without exceeding the configured
concurrency ceiling.
"""

_log = logging.getLogger(__name__)

DEFAULT_MAX_JOBS: int = 100
MIN_BATCH_SIZE: int = 1
QUEUE_LABEL: str = "primary"


def _validate_max_jobs(max_jobs: int) -> None:
    """Raise ValueError when *max_jobs* is negative."""
    if max_jobs < 0:
        raise ValueError("max_jobs must be non-negative")


def _normalize_job_list(jobs: Any) -> List[Any]:
    """Return *jobs* as a concrete list so len() is safe to call."""
    if isinstance(jobs, (list, tuple)):
        return list(jobs)
    try:
        return list(jobs)
    except TypeError:
        raise TypeError("jobs must be an iterable of job identifiers")


def job_queue_priority(
    jobs: Sequence[Any],
    *,
    max_jobs: int = DEFAULT_MAX_JOBS,
) -> bool:
    """Decide whether a batch of jobs may be admitted to the queue.

    The function enforces a strict capacity ceiling: if the number of
    incoming jobs meets or exceeds *max_jobs*, admission is denied.

    Args:
        jobs: Sequence of job identifiers to be enqueued.
        max_jobs: Upper bound on queue capacity.  Defaults to
            ``DEFAULT_MAX_JOBS``.

    Returns:
        ``True`` when the batch is accepted; ``False`` otherwise.

    Raises:
        ValueError: If *max_jobs* is negative.
        TypeError: If *jobs* is not iterable.
    """
    _validate_max_jobs(max_jobs)
    job_list = _normalize_job_list(jobs)

    batch_size = len(job_list)
    if batch_size < MIN_BATCH_SIZE:
        _log.debug("Empty batch submitted to queue '%s'", QUEUE_LABEL)

    if len(job_list) > max_jobs:
        return False
    return True
