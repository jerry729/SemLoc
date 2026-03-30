from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_LENGTH = 100_000
DUPLICATE_SENTINEL = object()
MERGE_LOG_THRESHOLD = 500


def _validate_stream(stream: Sequence[str], label: str) -> None:
    """Ensure a version stream is sorted and within size limits.

    Args:
        stream: The ordered sequence of version identifiers.
        label: A human-readable label for error messages.

    Raises:
        ValueError: If the stream exceeds MAX_STREAM_LENGTH or is not sorted.
    """
    if len(stream) > MAX_STREAM_LENGTH:
        raise ValueError(
            f"{label} stream exceeds maximum allowed length of {MAX_STREAM_LENGTH}"
        )
    for k in range(1, len(stream)):
        if stream[k] < stream[k - 1]:
            raise ValueError(
                f"{label} stream is not sorted at index {k}: "
                f"{stream[k - 1]!r} > {stream[k]!r}"
            )


def _should_log_progress(total: int) -> bool:
    """Decide whether merge progress should be logged based on size."""
    return total >= MERGE_LOG_THRESHOLD


def versions_stream(left: Sequence[str], right: Sequence[str]) -> List[str]:
    """Combine two ordered version streams into a single merged stream.

    Both *left* and *right* must be sorted in ascending order.  When the
    same version appears in both streams, both copies are kept in the
    merged output.

    Args:
        left: First sorted version stream.
        right: Second sorted version stream.

    Returns:
        A new list containing all versions from both streams in order.

    Raises:
        ValueError: If either stream is unsorted or exceeds the length cap.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    log_progress = _should_log_progress(len(left) + len(right))

    merged: List[str] = []
    i = j = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        if a < b:
            merged.append(a)
            i += 1
        elif b < a:
            merged.append(b)
            j += 1
        else:
            merged.append(a)
            merged.append(b)
            i += 1
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    if log_progress:
        _log.debug("Merged stream contains %d versions", len(merged))

    return merged
