# cbfl_runtime.py
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Per-test context (works for parameterized tests; each test has unique nodeid)
_current_test_id: ContextVar[Optional[str]] = ContextVar(
    "cbfl_current_test_id", default=None
)

# Store violations as a list of (cid, reason)
_violations: ContextVar[List[Tuple[str, str]]] = ContextVar(
    "cbfl_violations", default=[]
)

# --- Optional TUOW (temporal-until-overwritten) state, also per-test
_tuow_last: ContextVar[Dict[str, Any]] = ContextVar("cbfl_tuow_last", default={})


def set_test_id(test_id: str) -> None:
    """Call at the beginning of each test to isolate state."""
    _current_test_id.set(test_id)
    _violations.set([])
    _tuow_last.set({})


def get_test_id() -> Optional[str]:
    return _current_test_id.get()


def reset() -> None:
    """Clear violations and TUOW state for the current test."""
    _violations.set([])
    _tuow_last.set({})


def log(sut_id: str, cid: str, reason: str) -> None:
    v = _violations.get()
    # Ensure we don't accidentally share list object (defensive)
    if v is None:
        v = []
    v.append((sut_id, cid, reason))


def get() -> List[Tuple[str, str]]:
    return list(_violations.get() or [])


def check(sut_id: str, cid: str, reason: str, thunk) -> None:
    try:
        ok = bool(thunk())
        if not ok:
            log(sut_id, cid, reason)
    except Exception:
        log(sut_id, cid, reason)


# -----------------------------
# TUOW helpers (optional)
# -----------------------------


def tuow_write(cid: str, sut_id: str, key: str, value: Any) -> None:
    d = _tuow_last.get()
    if d is None:
        d = {}
    d[key] = value
    _tuow_last.set(d)


def tuow_kill(cid: str, sut_id: str, key: str) -> None:
    d = _tuow_last.get()
    if not d:
        return
    if key in d:
        del d[key]
    _tuow_last.set(d)


def tuow_read(cid: str, sut_id: str, key: str, value: Any) -> None:
    d = _tuow_last.get() or {}
    if key in d and value != d[key]:
        log(sut_id, cid, f"TUOW key={key} expected={d[key]} got={value}")
