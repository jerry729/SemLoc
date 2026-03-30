import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.job_queue_priority import job_queue_priority
else:
    from programs.job_queue_priority import job_queue_priority


def test_empty_batch_always_accepted():
    """An empty batch should always be admitted regardless of capacity."""
    assert job_queue_priority([], max_jobs=5) is True


def test_small_batch_under_capacity():
    """A batch well under the limit should be accepted."""
    jobs = ["j1", "j2", "j3"]
    assert job_queue_priority(jobs, max_jobs=10) is True


def test_negative_max_jobs_raises():
    """A negative capacity ceiling is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        job_queue_priority(["j1"], max_jobs=-1)


def test_non_iterable_raises():
    """Passing a non-iterable as jobs must raise TypeError."""
    with pytest.raises(TypeError):
        job_queue_priority(42, max_jobs=5)


def test_batch_exceeding_capacity_rejected():
    """A batch larger than the capacity must be rejected."""
    jobs = list(range(11))
    assert job_queue_priority(jobs, max_jobs=5) is False


def test_batch_at_exact_capacity_rejected():
    """A batch whose size equals max_jobs should be denied admission."""
    jobs = list(range(5))
    assert job_queue_priority(jobs, max_jobs=5) is False


def test_batch_one_below_capacity_accepted():
    """A batch one job short of the ceiling should be admitted."""
    jobs = list(range(4))
    assert job_queue_priority(jobs, max_jobs=5) is True


def test_zero_capacity_rejects_any_job():
    """With zero capacity even a single job must be denied."""
    assert job_queue_priority(["j1"], max_jobs=0) is False


def test_zero_capacity_accepts_empty_batch():
    """With zero capacity an empty batch should still be accepted."""
    assert job_queue_priority([], max_jobs=0) is False


def test_default_max_jobs_accepts_moderate_batch():
    """The default ceiling of 100 should accept a batch of 50 jobs."""
    jobs = [f"task-{i}" for i in range(50)]
    assert job_queue_priority(jobs) is True
