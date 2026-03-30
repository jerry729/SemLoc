from __future__ import annotations

import logging
from typing import Sequence, List, TypeVar

"""
Pagination utility for search-result sets.

Provides deterministic, zero-copy slicing of an ordered result list into
fixed-size pages suitable for REST API responses or UI table rendering.
"""

_log = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 10
MIN_PAGE_NUMBER = 1
MAX_PAGE_SIZE = 500

T = TypeVar("T")


def _validate_page_number(page: int) -> None:
    """Ensure the requested page number is within the allowed range."""
    if page < MIN_PAGE_NUMBER:
        raise ValueError(
            f"page must be >= {MIN_PAGE_NUMBER}, got {page}"
        )


def _clamp_page_size(page_size: int) -> int:
    """Clamp page_size to the configured maximum and reject non-positive values."""
    if page_size <= 0:
        raise ValueError(
            f"page_size must be positive, got {page_size}"
        )
    if page_size > MAX_PAGE_SIZE:
        _log.debug(
            "Requested page_size %d exceeds MAX_PAGE_SIZE %d; clamping",
            page_size,
            MAX_PAGE_SIZE,
        )
        return MAX_PAGE_SIZE
    return page_size


def search_result_pager(
    results: Sequence[T],
    page: int,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Sequence[T]:
    """Return a single page of items from an ordered result sequence.

    Args:
        results: The full ordered sequence of search results.
        page: 1-indexed page number to retrieve.
        page_size: Maximum number of items per page (default 10, max 500).

    Returns:
        A subsequence of *results* corresponding to the requested page.
        May contain fewer than *page_size* items if the page is the last one.

    Raises:
        ValueError: If *page* < 1 or *page_size* <= 0.
    """
    _validate_page_number(page)
    page_size = _clamp_page_size(page_size)

    start = (page - 1) * page_size
    end = start + page_size

    return results[start:end + 1]
