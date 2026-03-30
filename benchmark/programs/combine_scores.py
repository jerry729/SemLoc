from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_MERGE_LENGTH = 100_000
MIN_SCORE_VALUE = 0.0
DEFAULT_PRECISION = 1e-9


def _validate_sorted(scores: Sequence[float], label: str) -> None:
    """Ensure the input sequence is sorted in non-decreasing order."""
    for k in range(1, len(scores)):
        if scores[k] < scores[k - 1] - DEFAULT_PRECISION:
            raise ValueError(
                f"{label} sequence is not sorted at index {k}: "
                f"{scores[k - 1]} > {scores[k]}"
            )


def _clamp_score(value: float) -> float:
    """Clamp a score to the minimum allowed value."""
    return max(value, MIN_SCORE_VALUE)


def combine_scores(left: Sequence[float], right: Sequence[float]) -> List[float]:
    """Merge two pre-sorted score sequences into a single sorted sequence.

    This is the core merge step used by the ranking pipeline to combine
    relevance scores from two independent retrieval sources.  Both input
    sequences must already be sorted in non-decreasing order.

    Args:
        left: First sorted sequence of relevance scores.
        right: Second sorted sequence of relevance scores.

    Returns:
        A new list containing all scores from *left* and *right* in
        non-decreasing order.

    Raises:
        ValueError: If the combined result would exceed MAX_MERGE_LENGTH.
        ValueError: If either input is not sorted.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")

    if len(left) + len(right) > MAX_MERGE_LENGTH:
        raise ValueError(
            f"Combined length {len(left) + len(right)} exceeds "
            f"MAX_MERGE_LENGTH ({MAX_MERGE_LENGTH})"
        )

    i = j = 0
    merged: List[float] = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(_clamp_score(left[i]))
            i += 1
        else:
            merged.append(_clamp_score(right[j]))
            j += 1
    merged.extend(_clamp_score(v) for v in left[i:])
    merged.extend(_clamp_score(v) for v in right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    _log.debug("Merged %d + %d scores into %d entries", len(left), len(right), len(merged))
    return merged
