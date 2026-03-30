import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.gpu_memory_pool import gpu_memory_pool
else:
    from programs.gpu_memory_pool import gpu_memory_pool


def test_request_fits_with_large_headroom():
    """A small request against a mostly-empty pool should always be granted."""
    result = gpu_memory_pool([512, 512], 1024, capacity=1048576)
    assert result is True


def test_request_clearly_exceeds_capacity():
    """Requesting more memory than physically available must be denied."""
    result = gpu_memory_pool([512], 1048576, capacity=2048)
    assert result is False


def test_empty_pool_small_request():
    """An empty pool with a small request well within capacity should succeed."""
    result = gpu_memory_pool([], 512, capacity=4096)
    assert result is True


def test_zero_request_on_empty_pool():
    """Zero-byte allocation probes should always succeed on an empty pool."""
    result = gpu_memory_pool([], 0, capacity=4096)
    assert result is True


def test_negative_capacity_raises():
    """The pool must reject non-positive capacity values."""
    with pytest.raises(ValueError):
        gpu_memory_pool([], 100, capacity=-1)


def test_negative_request_raises():
    """Negative allocation requests are invalid and must be rejected."""
    with pytest.raises(ValueError):
        gpu_memory_pool([], -512, capacity=4096)


def test_request_exactly_fills_remaining_capacity():
    """When the request exactly consumes all remaining capacity the pool must deny it."""
    result = gpu_memory_pool([1024], 1024, capacity=2048)
    assert result is False


def test_request_fills_pool_from_empty():
    """A single request equal to the full capacity should be denied."""
    result = gpu_memory_pool([], 8192, capacity=8192)
    assert result is False


def test_used_equals_capacity_zero_request():
    """When the pool is already at capacity a zero-byte probe should be denied."""
    result = gpu_memory_pool([2048, 2048], 0, capacity=4096)
    assert result is False


def test_one_byte_below_capacity():
    """A request that leaves exactly one alignment unit free should succeed."""
    result = gpu_memory_pool([512], 512, capacity=1537)
    assert result is True
