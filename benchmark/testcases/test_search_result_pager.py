import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.search_result_pager import search_result_pager
else:
    from programs.search_result_pager import search_result_pager


def test_invalid_page_number_raises():
    """Requesting page 0 or negative must raise ValueError."""
    with pytest.raises(ValueError):
        search_result_pager(list(range(20)), 0)


def test_invalid_page_size_raises():
    """A non-positive page_size must raise ValueError."""
    with pytest.raises(ValueError):
        search_result_pager(list(range(20)), 1, page_size=0)


def test_empty_results_return_empty():
    """Paginating an empty collection returns an empty list regardless of page."""
    assert search_result_pager([], 1) == []


def test_page_beyond_results_returns_empty():
    """Requesting a page past the last available items yields an empty sequence."""
    data = list(range(5))
    assert search_result_pager(data, 100, page_size=5) == []


def test_first_page_default_size():
    """First page with default size returns exactly 10 items."""
    data = list(range(30))
    page = search_result_pager(data, 1)
    assert len(page) == 10
    assert list(page) == list(range(10))


def test_second_page_default_size():
    """Second page with default size returns items 10-19."""
    data = list(range(30))
    page = search_result_pager(data, 2)
    assert len(page) == 10
    assert list(page) == list(range(10, 20))


def test_custom_page_size_returns_exact_count():
    """With page_size=3 the returned page must contain exactly 3 items."""
    data = list(range(20))
    page = search_result_pager(data, 1, page_size=3)
    assert len(page) == 3
    assert list(page) == [0, 1, 2]


def test_last_partial_page_contains_remaining_items():
    """When results don't fill the last page, only the remainder is returned."""
    data = list(range(7))
    page = search_result_pager(data, 2, page_size=5)
    assert len(page) == 2
    assert list(page) == [5, 6]


def test_all_pages_cover_full_dataset():
    """Concatenating all pages must exactly reproduce the original dataset."""
    data = list(range(23))
    page_size = 5
    total_pages = (len(data) + page_size - 1) // page_size
    collected = []
    for p in range(1, total_pages + 1):
        collected.extend(search_result_pager(data, p, page_size=page_size))
    assert collected == data


def test_single_element_page():
    """A page_size of 1 returns exactly one element per page."""
    data = ["alpha", "beta", "gamma"]
    assert search_result_pager(data, 2, page_size=1) == ["beta"]
