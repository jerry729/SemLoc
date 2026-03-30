"""
baselines.py — SBFL and Delta Debugging evaluation baselines.

Provides two fault localization baselines for comparison with SemLoc CBFL:

SBFL (Spectrum-Based Fault Localization):
    Runs each test with line coverage tracking; computes Ochiai score per line
    using ef/ep/nf/np counts; reports suspicious line percentage.

DD (Delta Debugging):
    Applies DD2 algorithm over the set of reducible statements in the source;
    finds the minimal set of statements that still causes originally-failing
    tests to fail; reports that set as the suspicious percentage.

Usage as library:
    from baselines import sbfl_run, dd_run
    sbfl_result = sbfl_run(src_path, test_path, repo_root)
    dd_result   = dd_run(src_path, test_path, repo_root)

Usage as CLI (parallel runner over all programs in a dataset):
    python baselines.py <working_dir> [workers]

    working_dir must contain:
        programs/       — *.py source files
        testcases/      — test_<name>.py files
    Results written to: <working_dir>/results/baselines/<name>.json
"""

from __future__ import annotations

import ast
import json
import math
import os
import re
import signal
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def _run_with_timeout(cmd: List[str], timeout: int, **kwargs) -> subprocess.CompletedProcess:
    """Run a command in a new process group; kill the whole group on timeout."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
        **kwargs,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait()
        raise


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def count_executable_lines(src: str) -> int:
    """Count non-blank, non-comment lines as a proxy for inspectable code."""
    count = 0
    for line in src.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            count += 1
    return count


def get_test_outcomes(test_path: str, repo_root: str) -> Dict[str, bool]:
    """Run pytest and return {test_function_name: passed}."""
    try:
        result = _run_with_timeout(
            [sys.executable, "-m", "pytest", "-v", "--tb=no", "--disable-warnings", test_path],
            timeout=60, cwd=repo_root,
        )
    except subprocess.TimeoutExpired:
        return {}
    outcomes: Dict[str, bool] = {}
    for line in (result.stdout + result.stderr).splitlines():
        m = re.search(r"::(\S+)\s+(PASSED|FAILED)", line)
        if m:
            outcomes[m.group(1)] = (m.group(2) == "PASSED")
    return outcomes


def get_test_ids(test_path: str, repo_root: str) -> List[str]:
    """Return full pytest node IDs for all tests in test_path."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = repo_root + (":" + existing if existing else "")
    try:
        result = _run_with_timeout(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "--disable-warnings", "--tb=no", "-p", "conftest", test_path],
            timeout=30, cwd=repo_root, env=env,
        )
    except subprocess.TimeoutExpired:
        return []
    abs_test = os.path.abspath(test_path)
    test_dir = os.path.dirname(abs_test)
    test_file = os.path.basename(abs_test)
    ids = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.startswith("#") and not line.startswith("<"):
            raw = line.split()[0]
            # raw may be just "test_foo.py::class::method" (relative to cwd) or absolute.
            # Normalise to absolute so _coverage_for_test can find the file regardless of cwd.
            if not os.path.isabs(raw.split("::")[0]):
                raw = test_file + raw[raw.index("::"):]  # keep class/method, replace file part
                raw = abs_test + raw[len(test_file):]
            ids.append(raw)
    return ids


# ---------------------------------------------------------------------------
# SBFL
# ---------------------------------------------------------------------------

def _coverage_for_test(
    test_id: str,
    abs_src: str,
    repo_root: str,
) -> Tuple[bool, Set[int]]:
    """Run one test with coverage.py; return (passed, hit_lines_in_src)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_file = os.path.join(tmpdir, ".coverage")
        cov_json  = os.path.join(tmpdir, "cov.json")
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = repo_root + (":" + existing if existing else "")
        env["COVERAGE_FILE"] = data_file

        try:
            run_res = _run_with_timeout(
                [sys.executable, "-m", "coverage", "run",
                 "-m", "pytest", "-p", "conftest", test_id, "--tb=no", "-q"],
                timeout=30, env=env, cwd=repo_root,
            )
            passed = run_res.returncode == 0
        except subprocess.TimeoutExpired:
            return False, set()

        subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", cov_json],
            capture_output=True, text=True, env=env, cwd=repo_root,
        )

        hit_lines: Set[int] = set()
        if os.path.exists(cov_json):
            try:
                with open(cov_json) as f:
                    cov_data = json.load(f)
            except json.JSONDecodeError:
                cov_data = {}
            for fpath, fdata in cov_data.get("files", {}).items():
                norm = os.path.normpath(os.path.join(repo_root, fpath))
                if norm == os.path.normpath(abs_src):
                    hit_lines = set(fdata.get("executed_lines", []))
                    break

        return passed, hit_lines


def _ochiai(ef: int, nf: int, ep: int) -> float:
    denom = math.sqrt((ef + nf) * (ef + ep))
    return ef / denom if denom > 0 and ef > 0 else 0.0


def _tarantula(ef: int, nf: int, ep: int, np_: int) -> float:
    if ef + nf == 0:
        return 0.0
    fail_rate = ef / (ef + nf)
    pass_rate = ep / (ep + np_) if (ep + np_) > 0 else 0.0
    denom = fail_rate + pass_rate
    return fail_rate / denom if denom > 0 else 0.0


def sbfl_run(
    src_path: str,
    test_path: str,
    repo_root: Optional[str] = None,
    formula: str = "ochiai",
) -> Dict:
    """
    Spectrum-Based Fault Localization.

    For each test: run with coverage.py, collect hit lines and pass/fail outcome.
    Compute suspiciousness per line using ``formula`` (``"ochiai"`` or ``"tarantula"``).

    Returns dict with keys: line_scores, n_suspicious, pct_suspicious, n_fail, n_pass.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.abspath(__file__))

    src = open(src_path).read()
    n_exec = count_executable_lines(src)
    abs_src = os.path.realpath(src_path)  # resolve symlinks for coverage path matching

    test_ids = get_test_ids(test_path, repo_root)
    if not test_ids:
        return {"line_scores": {}, "n_suspicious": 0, "pct_suspicious": 0.0,
                "n_fail": 0, "n_pass": 0}

    ef_per_line: Dict[int, int] = {}
    ep_per_line: Dict[int, int] = {}
    n_fail = 0
    n_pass = 0

    for test_id in test_ids:
        passed, hit_lines = _coverage_for_test(test_id, abs_src, repo_root)
        if passed:
            n_pass += 1
            for ln in hit_lines:
                ep_per_line[ln] = ep_per_line.get(ln, 0) + 1
        else:
            n_fail += 1
            for ln in hit_lines:
                ef_per_line[ln] = ef_per_line.get(ln, 0) + 1

    line_scores: Dict[int, float] = {}
    all_lines = set(ef_per_line) | set(ep_per_line)
    for ln in all_lines:
        ef = ef_per_line.get(ln, 0)
        ep = ep_per_line.get(ln, 0)
        nf = n_fail - ef
        np_ = n_pass - ep
        if formula == "tarantula":
            score = _tarantula(ef, nf, ep, np_)
        else:
            score = _ochiai(ef, nf, ep)
        if score > 0:
            line_scores[ln] = score

    n_suspicious = len(line_scores)
    pct = 100.0 * n_suspicious / n_exec if n_exec else 0.0
    return {
        "line_scores": line_scores,
        "n_suspicious": n_suspicious,
        "pct_suspicious": round(pct, 1),
        "n_fail": n_fail,
        "n_pass": n_pass,
    }


# ---------------------------------------------------------------------------
# DD (Delta Debugging)
# ---------------------------------------------------------------------------

# Only reduce these statement types (never control-flow headers or imports).
_REDUCIBLE = (
    ast.Assign, ast.AugAssign, ast.AnnAssign,
    ast.Return, ast.Raise, ast.Assert, ast.Delete,
    ast.Expr, ast.Break, ast.Continue,
)


def _get_reducible_lines(src: str) -> List[int]:
    """Return sorted line numbers of reducible (simple, non-import) statements."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, _REDUCIBLE) and hasattr(node, "lineno"):
            lines.add(node.lineno)
    return sorted(lines)


class _StmtRemover(ast.NodeTransformer):
    """Replace reducible statements not in keep_lines with Pass()."""

    def __init__(self, keep_lines: Set[int]) -> None:
        self.keep_lines = keep_lines

    def _maybe_pass(self, node: ast.stmt) -> ast.stmt:
        if hasattr(node, "lineno") and node.lineno not in self.keep_lines:
            p = ast.Pass()
            ast.copy_location(p, node)
            ast.fix_missing_locations(p)
            return p
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Return(self, node: ast.Return) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Raise(self, node: ast.Raise) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Assert(self, node: ast.Assert) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Delete(self, node: ast.Delete) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Expr(self, node: ast.Expr) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Break(self, node: ast.Break) -> ast.stmt:
        return self._maybe_pass(node)

    def visit_Continue(self, node: ast.Continue) -> ast.stmt:
        return self._maybe_pass(node)


def _make_reduced_source(src: str, keep_lines: Set[int]) -> Optional[str]:
    """Produce reduced source with excluded statements replaced by pass."""
    try:
        tree = ast.parse(src)
        remover = _StmtRemover(keep_lines)
        new_tree = remover.visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)
    except Exception:
        return None


def _write_to_tmpdir(
    reduced_src: str,
    src_path: str,
    repo_root: str,
) -> Tuple[str, Dict[str, str]]:
    """Write reduced source to a temp dir mirroring the package structure."""
    tmpdir = tempfile.mkdtemp()
    abs_src = os.path.abspath(src_path)
    try:
        rel_path = os.path.relpath(abs_src, repo_root)
        if rel_path.startswith('..'):  # src outside repo_root — use basename only
            rel_path = os.path.basename(src_path)
    except ValueError:
        rel_path = os.path.basename(src_path)

    patched_path = os.path.join(tmpdir, rel_path)
    pkg_dir = os.path.dirname(patched_path)
    os.makedirs(pkg_dir, exist_ok=True)
    with open(patched_path, "w") as f:
        f.write(reduced_src)

    # Ensure regular package (not namespace package) to prevent import merging.
    cur = pkg_dir
    while cur != tmpdir:
        init = os.path.join(cur, "__init__.py")
        if not os.path.exists(init):
            open(init, "w").close()
        cur = os.path.dirname(cur)

    env = {**os.environ}
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = tmpdir + (":" + existing if existing else "")
    return tmpdir, env


def _test_config(
    keep_lines: Set[int],
    src: str,
    src_path: str,
    test_path: str,
    failing_test_names: Set[str],
    passing_test_names: Set[str],
    repo_root: str,
) -> bool:
    """
    Return True iff this configuration preserves the original failure behaviour:
      - All originally-failing tests still FAIL
      - All originally-passing tests still PASS
    """
    reduced_src = _make_reduced_source(src, keep_lines)
    if reduced_src is None:
        return False

    tmpdir, env = _write_to_tmpdir(reduced_src, src_path, repo_root)
    try:
        result = _run_with_timeout(
            [sys.executable, "-m", "pytest", "-v", "--tb=no",
             "--disable-warnings", test_path],
            timeout=30, env=env, cwd=repo_root,
        )
        current_passing: Set[str] = set()
        current_failing: Set[str] = set()
        for line in (result.stdout + result.stderr).splitlines():
            m = re.search(r"::(\S+)\s+(PASSED|FAILED)", line)
            if m:
                (current_passing if m.group(2) == "PASSED" else current_failing).add(m.group(1))
        return (failing_test_names <= current_failing and
                passing_test_names <= current_passing)
    except subprocess.TimeoutExpired:
        return False
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def _dd2(
    config: List[int],
    test_fn,
    max_iters: int = 100,
) -> Tuple[List[int], int]:
    """
    DD2 minimisation algorithm.

    config   : current failure-inducing configuration (list of statement lines)
    test_fn  : callable(Set[int]) -> bool — True iff that subset still causes failure
    max_iters: hard limit on test_fn calls to bound runtime

    Returns (minimal_config, n_test_calls).
    """
    iters = [0]

    def call(s: Set[int]) -> bool:
        if iters[0] >= max_iters:
            return False
        iters[0] += 1
        return test_fn(s)

    n = 2
    while len(config) >= 2:
        step = max(1, len(config) // n)
        subsets = [config[i: i + step] for i in range(0, len(config), step)]

        reduced = False
        for subset in subsets:
            if call(set(subset)):
                config = list(subset)
                n = max(n - 1, 2)
                reduced = True
                break
            complement = [x for x in config if x not in set(subset)]
            if complement and call(set(complement)):
                config = complement
                n = max(n - 1, 2)
                reduced = True
                break

        if not reduced:
            if n >= len(config):
                break
            n = min(2 * n, len(config))

        if iters[0] >= max_iters:
            break

    return config, iters[0]


def dd_run(
    src_path: str,
    test_path: str,
    repo_root: Optional[str] = None,
    max_iterations: int = 80,
) -> Dict:
    """
    Delta Debugging fault localization baseline.

    Finds the minimal subset of reducible statements that preserves the original
    test outcome split (failing tests still fail, passing tests still pass).

    Returns dict with keys: minimal_lines, n_suspicious, pct_suspicious,
                             dd_iterations, n_reducible.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.abspath(__file__))

    src = open(src_path).read()
    n_exec = count_executable_lines(src)

    outcomes = get_test_outcomes(test_path, repo_root)
    failing_names = {name for name, passed in outcomes.items() if not passed}
    passing_names = {name for name, passed in outcomes.items() if passed}
    if not failing_names:
        return {"minimal_lines": [], "n_suspicious": 0, "pct_suspicious": 0.0,
                "dd_iterations": 0, "n_reducible": 0}

    stmt_lines = _get_reducible_lines(src)
    if not stmt_lines:
        return {"minimal_lines": [], "n_suspicious": 0, "pct_suspicious": 0.0,
                "dd_iterations": 0, "n_reducible": 0}

    full_set = set(stmt_lines)
    if not _test_config(full_set, src, src_path, test_path, failing_names,
                        passing_names, repo_root):
        # Fallback: report all reducible lines as suspicious.
        return {"minimal_lines": stmt_lines, "n_suspicious": len(stmt_lines),
                "pct_suspicious": round(100.0 * len(stmt_lines) / n_exec, 1),
                "dd_iterations": 1, "n_reducible": len(stmt_lines)}

    def test_fn(keep: Set[int]) -> bool:
        return _test_config(keep, src, src_path, test_path, failing_names,
                            passing_names, repo_root)

    minimal, n_iters = _dd2(stmt_lines, test_fn, max_iters=max_iterations)

    n_suspicious = len(minimal)
    pct = 100.0 * n_suspicious / n_exec if n_exec else 0.0
    return {
        "minimal_lines": minimal,
        "n_suspicious": n_suspicious,
        "pct_suspicious": round(pct, 1),
        "dd_iterations": n_iters,
        "n_reducible": len(stmt_lines),
    }


# ---------------------------------------------------------------------------
# Parallel runner (CLI entry point)
# ---------------------------------------------------------------------------

def _compute_one(args):
    func_name, src_path, test_path, repo_root, cached_path = args
    if os.path.exists(cached_path):
        return func_name, "cached", None
    try:
        sbfl_result = sbfl_run(src_path, test_path, repo_root)
        dd_result   = dd_run(src_path, test_path, repo_root, max_iterations=80)
        entry = {"sbfl": sbfl_result, "dd": dd_result}
        with open(cached_path, "w") as f:
            json.dump(entry, f, indent=2)
        return func_name, "ok", entry
    except Exception as e:
        return func_name, f"error: {e}", None


def main():
    """Run SBFL + DD baselines in parallel over all programs in a working directory."""
    working_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    workers     = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    programs_dir  = os.path.join(working_dir, "programs")
    test_dir      = os.path.join(working_dir, "testcases")
    baselines_dir = os.path.join(working_dir, "results", "baselines")
    os.makedirs(baselines_dir, exist_ok=True)

    repo_root = os.path.dirname(os.path.abspath(__file__))

    tasks = []
    for src_path in sorted(Path(programs_dir).glob("*.py")):
        func_name   = src_path.stem
        test_path   = os.path.join(test_dir, f"test_{func_name}.py")
        cached_path = os.path.join(baselines_dir, f"{func_name}.json")
        if not os.path.exists(test_path):
            continue
        tasks.append((func_name, str(src_path), test_path, repo_root, cached_path))

    total  = len(tasks)
    cached = sum(1 for *_, cp in tasks if os.path.exists(cp))
    print(f"[baselines] {total} programs, {cached} already cached, "
          f"{total - cached} to compute  (workers={workers})")

    done = cached
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_compute_one, t): t[0] for t in tasks}
        for fut in as_completed(futures):
            func_name, status, _ = fut.result()
            if status != "cached":
                done += 1
                print(f"[{done}/{total}] {func_name}: {status}", flush=True)

    print(f"\nDone. {done}/{total} programs have baselines cached.")
    print(f"Results in: {baselines_dir}")


if __name__ == "__main__":
    main()
