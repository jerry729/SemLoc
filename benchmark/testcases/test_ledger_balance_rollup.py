import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.ledger_balance_rollup import ledger_balance_rollup
else:
    from programs.ledger_balance_rollup import ledger_balance_rollup


def test_empty_ledger_returns_zero():
    """An empty ledger with no entries should yield a zero balance."""
    result = ledger_balance_rollup([])
    assert abs(result - 0.0) < 1e-9


def test_single_credit_entry():
    """A single credit entry should increase the balance by the entry amount."""
    result = ledger_balance_rollup([(500.0, "credit")])
    assert abs(result - 500.0) < 1e-9


def test_multiple_credits_accumulate():
    """Multiple credit entries should sum to the total credited amount."""
    entries = [(100.0, "credit"), (250.50, "credit"), (49.50, "credit")]
    result = ledger_balance_rollup(entries)
    assert abs(result - 400.0) < 1e-9


def test_negative_amount_raises_value_error():
    """Ledger entries with negative amounts are invalid and must be rejected."""
    with pytest.raises(ValueError):
        ledger_balance_rollup([(-10.0, "credit")])


def test_unknown_kind_raises_value_error():
    """Entry kinds other than credit and debit are not supported."""
    with pytest.raises(ValueError):
        ledger_balance_rollup([(100.0, "refund")])


def test_single_debit_produces_negative_balance():
    """A single debit with no prior credits should result in a negative balance."""
    result = ledger_balance_rollup([(200.0, "debit")])
    assert abs(result - (-200.0)) < 1e-9


def test_credits_and_debits_net_balance():
    """Credits and debits together should yield the correct net balance."""
    entries = [(1000.0, "credit"), (300.0, "debit"), (50.0, "debit")]
    result = ledger_balance_rollup(entries)
    assert abs(result - 650.0) < 1e-9


def test_equal_credit_and_debit_zero_balance():
    """Equal credit and debit amounts should cancel out to zero."""
    entries = [(750.0, "credit"), (750.0, "debit")]
    result = ledger_balance_rollup(entries)
    assert abs(result - 0.0) < 1e-9


def test_debit_exceeds_credit_negative_result():
    """When total debits exceed credits, the balance should be negative."""
    entries = [
        (100.0, "credit"),
        (200.0, "debit"),
        (50.0, "credit"),
        (400.0, "debit"),
    ]
    result = ledger_balance_rollup(entries)
    assert abs(result - (-450.0)) < 1e-9


def test_large_mixed_ledger_balance():
    """A realistic mixed ledger of many transactions should compute the correct running total."""
    entries = [
        (5000.00, "credit"),
        (1200.00, "debit"),
        (300.00, "credit"),
        (800.00, "debit"),
        (150.75, "debit"),
        (2000.00, "credit"),
    ]
    expected = 5000.00 - 1200.00 + 300.00 - 800.00 - 150.75 + 2000.00
    result = ledger_balance_rollup(entries)
    assert abs(result - expected) < 1e-9
