import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.feature_flag_rollout import feature_flag_rollout
else:
    from programs.feature_flag_rollout import feature_flag_rollout


def test_invalid_percentage_above_one():
    """Rollout percentage above 1.0 must be rejected."""
    with pytest.raises(ValueError):
        feature_flag_rollout("user_42", percentage=1.5)


def test_invalid_percentage_negative():
    """Rollout percentage below 0 must be rejected."""
    with pytest.raises(ValueError):
        feature_flag_rollout("user_42", percentage=-0.1)


def test_full_rollout_always_enrolled():
    """With 100%% rollout every user must be enrolled."""
    users = [f"user_{i}" for i in range(200)]
    results = [feature_flag_rollout(uid, percentage=1.0) for uid in users]
    assert all(results)


def test_zero_rollout_never_enrolled():
    """With 0%% rollout no user should be enrolled."""
    users = [f"user_{i}" for i in range(200)]
    results = [feature_flag_rollout(uid, percentage=0.0) for uid in users]
    assert not any(results)


def test_deterministic_for_same_user():
    """The decision for a given user must be stable across repeated calls."""
    result_a = feature_flag_rollout("stable_user", percentage=0.5)
    result_b = feature_flag_rollout("stable_user", percentage=0.5)
    assert result_a == result_b


def test_return_type_is_bool():
    """The function must return a boolean value."""
    result = feature_flag_rollout(12345, percentage=0.5)
    assert isinstance(result, bool)


def test_enrolled_fraction_roughly_matches_percentage():
    """Over a large population the enrolled fraction should approximate the rollout percentage."""
    pct = 0.50
    users = list(range(10000))
    enrolled = sum(feature_flag_rollout(uid, percentage=pct) for uid in users)
    ratio = enrolled / len(users)
    assert abs(ratio - pct) < 0.10


def test_increasing_percentage_monotonically_includes_more_users():
    """Raising the rollout percentage must never decrease the enrolled set."""
    users = [f"id_{i}" for i in range(500)]
    enrolled_20 = {u for u in users if feature_flag_rollout(u, percentage=0.2)}
    enrolled_60 = {u for u in users if feature_flag_rollout(u, percentage=0.6)}
    assert enrolled_20.issubset(enrolled_60)


def test_small_rollout_enrolls_some_users():
    """A 10%% rollout over many users should enroll a non-trivial number."""
    users = list(range(5000))
    enrolled = sum(feature_flag_rollout(uid, percentage=0.10) for uid in users)
    ratio = enrolled / len(users)
    assert 0.02 < ratio < 0.20


def test_half_rollout_symmetry():
    """At 50%% rollout roughly half the user base should be enrolled."""
    users = list(range(10000))
    enrolled = sum(feature_flag_rollout(uid, percentage=0.5) for uid in users)
    ratio = enrolled / len(users)
    assert 0.35 < ratio < 0.65
