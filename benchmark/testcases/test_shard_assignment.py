import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shard_assignment import shard_assignment
else:
    from programs.shard_assignment import shard_assignment


def test_empty_key_list_returns_empty_buckets():
    """An empty input should produce the correct number of empty shards."""
    result = shard_assignment([], shards=3)
    assert len(result) == 3
    assert all(bucket == [] for bucket in result)


def test_single_shard_collects_all_keys():
    """With one shard, every key must land in that single bucket."""
    keys = ["alpha", "beta", "gamma"]
    result = shard_assignment(keys, shards=1)
    assert len(result) == 1
    assert set(result[0]) == set(keys)


def test_all_keys_are_preserved():
    """The union of all shards must equal the original key set."""
    keys = ["x", "y", "z", "w", "v"]
    result = shard_assignment(keys, shards=3)
    flattened = [k for bucket in result for k in bucket]
    assert sorted(flattened) == sorted(keys)


def test_negative_shard_count_raises():
    """A non-positive shard count should raise ValueError."""
    with pytest.raises(ValueError):
        shard_assignment(["a"], shards=0)


def test_default_shard_count_is_four():
    """When shards is not specified, the default of four should be used."""
    result = shard_assignment(["key1"])
    assert len(result) == 4


def test_single_shard_keys_sorted():
    """Keys within a single-shard assignment must be in sorted order."""
    keys = ["cherry", "apple", "banana"]
    result = shard_assignment(keys, shards=1)
    assert result[0] == sorted(keys)


def test_each_bucket_is_sorted():
    """Every shard bucket must return its keys in sorted order."""
    keys = ["delta", "alpha", "echo", "bravo", "charlie", "foxtrot"]
    result = shard_assignment(keys, shards=3)
    for bucket in result:
        assert bucket == sorted(bucket)


def test_deterministic_placement():
    """Repeated calls with the same keys must yield identical results."""
    keys = ["node-a", "node-b", "node-c", "node-d"]
    r1 = shard_assignment(keys, shards=4)
    r2 = shard_assignment(keys, shards=4)
    assert r1 == r2


def test_large_input_sorted_per_bucket():
    """For a larger key set, each bucket should still be individually sorted."""
    keys = [f"item-{i:04d}" for i in range(100, 0, -1)]
    result = shard_assignment(keys, shards=5)
    for bucket in result:
        assert bucket == sorted(bucket)


def test_two_shards_sorted_output():
    """With two shards and reversed input, each bucket must be sorted."""
    keys = ["z", "y", "x", "w", "v", "u"]
    result = shard_assignment(keys, shards=2)
    for bucket in result:
        assert bucket == sorted(bucket)
