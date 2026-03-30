import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.lr_warmup_schedule import lr_warmup_schedule
else:
    from programs.lr_warmup_schedule import lr_warmup_schedule


def test_negative_step_raises():
    """A negative training step is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        lr_warmup_schedule(-1)


def test_zero_warmup_steps_raises():
    """Zero warmup steps is not a valid configuration."""
    with pytest.raises(ValueError):
        lr_warmup_schedule(0, warmup_steps=0)


def test_negative_warmup_steps_raises():
    """Negative warmup_steps is not a valid configuration."""
    with pytest.raises(ValueError):
        lr_warmup_schedule(5, warmup_steps=-10)


def test_well_past_warmup_returns_base_lr():
    """After warmup is complete, the schedule should return the full base learning rate."""
    lr = lr_warmup_schedule(500, base_lr=0.01, warmup_steps=100)
    assert abs(lr - 0.01) < 1e-9


def test_midpoint_warmup():
    """At the midpoint of warmup, the learning rate should be half the base rate."""
    lr = lr_warmup_schedule(50, base_lr=0.01, warmup_steps=100)
    assert abs(lr - 0.005) < 1e-9


def test_step_zero_returns_zero_lr():
    """At step 0, before any training has occurred, the learning rate should be zero."""
    lr = lr_warmup_schedule(0, base_lr=0.01, warmup_steps=100)
    assert abs(lr - 0.0) < 1e-9


def test_last_warmup_step_returns_base_lr():
    """At the final warmup step, the learning rate should exactly equal base_lr."""
    lr = lr_warmup_schedule(100, base_lr=0.01, warmup_steps=100)
    assert abs(lr - 0.01) < 1e-9


def test_step_one_returns_one_percent():
    """At step 1 with 100 warmup steps, the rate should be 1% of base_lr."""
    lr = lr_warmup_schedule(1, base_lr=0.01, warmup_steps=100)
    assert abs(lr - 0.0001) < 1e-9


def test_linear_monotonicity():
    """The learning rate must increase monotonically during warmup."""
    rates = [lr_warmup_schedule(s, base_lr=0.1, warmup_steps=10) for s in range(12)]
    for i in range(1, len(rates)):
        assert rates[i] >= rates[i - 1] - 1e-12


def test_quarter_warmup():
    """At 25% through warmup, the learning rate should be 25% of base_lr."""
    lr = lr_warmup_schedule(25, base_lr=0.02, warmup_steps=100)
    assert abs(lr - 0.005) < 1e-9
