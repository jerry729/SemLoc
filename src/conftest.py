# tests/conftest.py
import os
import json
import pytest

_cbfl = None

def pytest_addoption(parser):
    group = parser.getgroup("inst")
    group.addoption("--inst", 
                    action="store_true", 
                    default=False, 
                    help="Run tests on instrumented SUT and enable violations collection.")
    group.addoption("--cbfl-report",
                    action="store",
                    default=None,
                    help="Path to CBFL JSONL report file (default: root/.pytest_cache/cbfl/cbfl_violations.jsonl).")


def _enabled(config: pytest.Config) -> bool:
    return bool(config.getoption("--inst") or os.environ.get("CBFL_ENABLED") == "1")


def pytest_configure(config: pytest.Config):
    global _cbfl
    pytest.inst = _enabled(config)
    if not _enabled(config):
        return 
    try:
        import cbfl_runtime as cbfl_runtime
        _cbfl=cbfl_runtime
    except Exception as e:
        raise pytest.UsageError(
            "CBFL is enabled but cbfl_runtime cannot be imported. "
            "Make sure cbfl_runtime.py is on PYTHONPATH."
        ) from e

def _get_report_path(config: pytest.Config) -> str:
    # user override
    p = config.getoption("--cbfl-report") or os.environ.get("CBFL_REPORT")
    
    if not p:
        cache_dir = getattr(config, "cache", None)
        if cache_dir is not None:
            root = str(cache_dir._cachedir)
        else:
            root = os.getcwd()
        p = os.path.join(root, "cbfl", "cbfl_violations.jsonl")

    # xdist: write per worker to avoid file races
    wid = os.environ.get("PYTEST_XDIST_WORKER")  # e.g., "gw0"
    if wid:
        root, ext = os.path.splitext(p)
        ext = ext if ext else ".jsonl"
        return f"{root}.{wid}{ext}"
    return p


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item):
    # Set per-test context (nodeid is unique even for parametrization)
    if _cbfl is None:
        return 
    _cbfl.set_test_id(item.nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    rep = outcome.get_result()

    if _cbfl is None:
        return
    # Only record once per test (the actual call phase)
    if rep.when != "call":
        return

    violations = [{"sut": sut, "cid": cid, "reason": reason} for sut, cid, reason in _cbfl.get()]

    record = {
        "nodeid": item.nodeid,
        "outcome": rep.outcome,  # "passed" | "failed" | "skipped"
        "duration": rep.duration,
        "violations": violations,
        "longrepr": str(rep.longrepr) if rep.failed else None,
    }

    path = _get_report_path(item.config)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
