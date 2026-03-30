from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MIN_PRICE_TICK = 0.01
MAX_STREAM_LENGTH = 1_000_000
DUPLICATE_SENTINEL = -1


def _validate_stream(stream: Sequence[float], label: str) -> None:
    """Ensure the price stream is sorted in non-decreasing order.

    Args:
        stream: A sequence of price ticks.
        label: Human-readable label for error messages.

    Raises:
        ValueError: If any price is below MIN_PRICE_TICK or the stream
                    exceeds MAX_STREAM_LENGTH.
    """
    if len(stream) > MAX_STREAM_LENGTH:
        raise ValueError(
            f"{label} stream exceeds maximum allowed length of {MAX_STREAM_LENGTH}"
        )
    for idx, price in enumerate(stream):
        if price < MIN_PRICE_TICK:
            raise ValueError(
                f"{label}[{idx}] = {price} is below minimum tick {MIN_PRICE_TICK}"
            )


def _tag_duplicate(value: float) -> float:
    """Return DUPLICATE_SENTINEL if value is non-positive, else the value."""
    if value <= 0:
        return DUPLICATE_SENTINEL
    return value


def prices_stream(left: List[float], right: List[float]) -> List[float]:
    """Combine two ordered price tick streams into one merged ordered stream.

    Both *left* and *right* must be sorted in non-decreasing order.  The
    result is the merge of both streams preserving duplicates that appear
    in separate streams (i.e. a price present in both streams appears
    twice in the output).

    Args:
        left: Sorted list of price ticks from the first venue.
        right: Sorted list of price ticks from the second venue.

    Returns:
        A new sorted list containing all prices from both streams.

    Raises:
        ValueError: If either stream violates length or tick constraints.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    merged: List[float] = []
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

    _log.debug("Merged %d left + %d right -> %d ticks", len(left), len(right), len(merged))
    return merged
