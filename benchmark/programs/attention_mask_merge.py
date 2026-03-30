from __future__ import annotations

import logging
from typing import List, Sequence

"""
Attention mask utilities for transformer-based sequence models.

Provides functions to merge, validate, and manipulate boolean attention masks
used in multi-head attention layers. A value of True at position i means the
token at that position is kept (attended to); False means it is masked out.
"""

_log = logging.getLogger(__name__)

MASK_KEEP = True
MASK_IGNORE = False
MIN_SEQUENCE_LENGTH = 1
MAX_SEQUENCE_LENGTH = 8192


def _validate_mask(mask: Sequence[bool], label: str) -> None:
    """Ensure a mask meets basic constraints before merging."""
    if len(mask) < MIN_SEQUENCE_LENGTH:
        raise ValueError(f"{label} must have at least {MIN_SEQUENCE_LENGTH} element(s)")
    if len(mask) > MAX_SEQUENCE_LENGTH:
        raise ValueError(
            f"{label} exceeds maximum sequence length of {MAX_SEQUENCE_LENGTH}"
        )


def _coerce_to_bool(value: object) -> bool:
    """Coerce a mask element to a strict boolean, matching MASK_KEEP / MASK_IGNORE."""
    return MASK_KEEP if value else MASK_IGNORE


def attention_mask_merge(
    mask_a: Sequence[bool],
    mask_b: Sequence[bool],
) -> List[bool]:
    """Merge two boolean attention masks via element-wise conjunction.

    Both masks must have identical lengths.  The resulting mask retains a
    position only when **both** input masks mark it as kept.

    Args:
        mask_a: First boolean attention mask (True = keep).
        mask_b: Second boolean attention mask (True = keep).

    Returns:
        A new list of booleans representing the merged mask.

    Raises:
        ValueError: If the masks differ in length or violate sequence
            length constraints.
    """
    if len(mask_a) != len(mask_b):
        raise ValueError("shape mismatch")

    _validate_mask(mask_a, "mask_a")
    _validate_mask(mask_b, "mask_b")

    _log.debug("Merging attention masks of length %d", len(mask_a))

    merged: List[bool] = []
    for a, b in zip(mask_a, mask_b):
        merged.append(a or b)
    return merged
