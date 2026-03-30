"""
bip_runner.py — BugsInPy checkout and SemLoc pipeline runner.

Combines two functions:
  1. Checkout a BugsInPy bug at its buggy commit (from bip_checkout.py)
  2. Run SemLoc on a checked-out BugsInPy project (from bip_semloc.py)

Usage:
    # Checkout a bug
    python bip_runner.py checkout pandas_1 --workdir /tmp/bip
    python bip_runner.py checkout pandas_1 --workdir /tmp/bip --faulty-lines

    # Run SemLoc on a checked-out bug
    python bip_runner.py run pandas_1 \\
        --function "pandas.core.dtypes.common.is_string_dtype" \\
        --checkout /tmp/bip/pandas_1 \\
        --test-file tests/api/test_types.py \\
        --out results/RQ3/semloc/pandas_1.json

    # Checkout then immediately run
    python bip_runner.py checkout-and-run pandas_1 \\
        --function "pandas.core.dtypes.common.is_string_dtype" \\
        --workdir /tmp/bip \\
        --out results/RQ3/semloc/pandas_1.json
"""

from __future__ import annotations

import ast
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure src/ is on the path for SemLoc imports
_SRC_ROOT = Path(__file__).parent
sys.path.insert(0, str(_SRC_ROOT))


# ===========================================================================
# Part 1: BugsInPy checkout (bip_checkout.py)
# ===========================================================================

PROJECT_REPOS: Dict[str, str] = {
    "PySnooper":    "https://github.com/cool-RR/PySnooper",
    "ansible":      "https://github.com/ansible/ansible",
    "black":        "https://github.com/psf/black",
    "cookiecutter": "https://github.com/cookiecutter/cookiecutter",
    "fastapi":      "https://github.com/tiangolo/fastapi",
    "httpie":       "https://github.com/httpie/httpie",
    "keras":        "https://github.com/keras-team/keras",
    "luigi":        "https://github.com/spotify/luigi",
    "matplotlib":   "https://github.com/matplotlib/matplotlib",
    "pandas":       "https://github.com/pandas-dev/pandas",
    "sanic":        "https://github.com/sanic-org/sanic",
    "scrapy":       "https://github.com/scrapy/scrapy",
    "spacy":        "https://github.com/explosion/spaCy",
    "thefuck":      "https://github.com/nvbn/thefuck",
    "tornado":      "https://github.com/tornadoweb/tornado",
    "youtube-dl":   "https://github.com/ytdl-org/youtube-dl",
}

BIP_BUG_INFO_URL = (
    "https://raw.githubusercontent.com/soarsmu/BugsInPy/master/"
    "projects/{project}/bugs/{n}/bug.info"
)


def _parse_bug_info(text: str) -> Dict[str, str]:
    """Parse BugsInPy bug.info key=value format (handles spaces around '=')."""
    result = {}
    for line in text.splitlines():
        m = re.match(r'^(\w+)\s*=\s*"([^"]*)"', line.strip())
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def get_bug_info(bug_id: str, cache_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Fetch bug.info for a BugsInPy bug.

    Returns dict with keys: python_version, buggy_commit_id, fixed_commit_id, test_file.
    """
    m = re.match(r'^(.+?)_(\d+)$', bug_id)
    if not m:
        raise ValueError(f"Invalid bug_id format: {bug_id!r} (expected 'project_N')")
    project, n = m.group(1), m.group(2)

    if cache_dir:
        cache_path = os.path.join(cache_dir, f"{bug_id}_bug.info")
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                return _parse_bug_info(f.read())

    url = BIP_BUG_INFO_URL.format(project=project, n=n)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch bug.info for {bug_id} from {url}: {e}")

    info = _parse_bug_info(text)

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{bug_id}_bug.info")
        with open(cache_path, "w") as f:
            f.write(text)

    return info


def _run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def checkout_bug(
    bug_id: str,
    workdir: str = "/tmp/bip_checkouts",
    cache_dir: Optional[str] = None,
    force: bool = False,
) -> Dict[str, str]:
    """
    Checkout a BugsInPy bug at its buggy commit.

    Returns: {checkout_dir, test_file, buggy_commit, fixed_commit, project}
    """
    m = re.match(r'^(.+?)_(\d+)$', bug_id)
    if not m:
        raise ValueError(f"Invalid bug_id: {bug_id!r}")
    project = m.group(1)

    if project not in PROJECT_REPOS:
        raise ValueError(f"Unknown project {project!r}. Known: {list(PROJECT_REPOS)}")

    repo_url = PROJECT_REPOS[project]
    checkout_dir = os.path.join(workdir, bug_id)

    bip_cache = os.path.join(workdir, ".bug_info_cache")
    info = get_bug_info(bug_id, cache_dir=bip_cache)
    buggy_commit = info["buggy_commit_id"]
    test_file = info.get("test_file", "")

    if os.path.exists(checkout_dir) and not force:
        result = _run(["git", "rev-parse", "HEAD"], cwd=checkout_dir, check=False)
        if result.returncode == 0 and result.stdout.strip().startswith(buggy_commit[:6]):
            print(f"[bip_runner] {bug_id} already checked out at {checkout_dir}")
            return {
                "checkout_dir": checkout_dir,
                "test_file": test_file,
                "buggy_commit": buggy_commit,
                "project": project,
            }

    os.makedirs(workdir, exist_ok=True)

    if not os.path.exists(os.path.join(checkout_dir, ".git")):
        print(f"[bip_runner] Cloning {repo_url} ...")
        _run(["git", "clone", repo_url, checkout_dir])
    else:
        print(f"[bip_runner] Fetching {repo_url} ...")
        _run(["git", "fetch", "--all"], cwd=checkout_dir)

    print(f"[bip_runner] Checking out buggy commit {buggy_commit} ...")
    _run(["git", "checkout", buggy_commit], cwd=checkout_dir)

    fixed_commit = info.get("fixed_commit_id", "").strip()
    if fixed_commit and test_file:
        print(f"[bip_runner] Applying test file {test_file!r} from fixed commit ...")
        r = _run(
            ["git", "checkout", fixed_commit, "--", test_file],
            cwd=checkout_dir, check=False
        )
        if r.returncode != 0:
            print(f"[bip_runner] Warning: could not apply fixed test file: {r.stderr.strip()}")

    return {
        "checkout_dir": checkout_dir,
        "test_file": test_file,
        "buggy_commit": buggy_commit,
        "fixed_commit": fixed_commit,
        "project": project,
    }


def get_faulty_lines_from_diff(bug_id: str, checkout_dir: str) -> Dict[str, list]:
    """
    Compute ground-truth faulty lines by diffing buggy vs fixed commit.
    Returns: {relative_file_path: [line_no, ...]}
    """
    bip_cache = os.path.join(os.path.dirname(checkout_dir), ".bug_info_cache")
    info = get_bug_info(bug_id, cache_dir=bip_cache)
    buggy_commit = info["buggy_commit_id"]
    fixed_commit = info["fixed_commit_id"]

    result = _run(
        ["git", "diff", "--unified=0", buggy_commit, fixed_commit, "--", "*.py"],
        cwd=checkout_dir, check=False
    )
    if result.returncode != 0:
        return {}

    faulty: Dict[str, list] = {}
    current_file = None

    for line in result.stdout.splitlines():
        m = re.match(r'^--- a/(.+)$', line)
        if m:
            current_file = m.group(1)
            faulty.setdefault(current_file, [])
            continue
        m = re.match(r'^@@ -(\d+)(?:,(\d+))? \+', line)
        if m and current_file:
            old_start = int(m.group(1))
            old_count = int(m.group(2) or 1)
            for ln in range(old_start, old_start + old_count):
                if ln not in faulty[current_file]:
                    faulty[current_file].append(ln)

    return {f: sorted(lns) for f, lns in faulty.items() if lns}


# ===========================================================================
# Part 2: SemLoc pipeline on BugsInPy (bip_semloc.py)
# ===========================================================================

from constraint_inference import query_llm_for_constraints, _extract_fn_with_linenos
from instrumentation import Instrumenter, parse_constraints
from spectrum import (
    load_violations,
    deduplicate_records,
    build_matrix,
    score_constraints,
    attribute_to_statements,
    rank_constraints,
    rank_lines,
    find_anchor_lines,
)
import cbfl_runtime


def _parse_qualified_name(predicted: str) -> Tuple[Optional[str], str]:
    """Split 'module.ClassName.method' → (ClassName or None, method)."""
    parts = predicted.rstrip("()").split(".")
    func_name = parts[-1]
    class_name = parts[-2] if len(parts) >= 2 and parts[-2][0].isupper() else None
    return class_name, func_name


def find_function_in_file(
    src_path: str, function_name: str, class_name: Optional[str] = None
) -> Optional[Tuple[str, int, int]]:
    """Find a function (optionally inside a class) in a Python source file."""
    with open(src_path, "r", errors="replace") as f:
        src = f.read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    lines = src.splitlines()

    def _snippet(node) -> str:
        return "\n".join(lines[node.lineno - 1 : node.end_lineno])

    if class_name:
        for cls_node in ast.walk(tree):
            if isinstance(cls_node, ast.ClassDef) and cls_node.name == class_name:
                for fn_node in cls_node.body:
                    if (
                        isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and fn_node.name == function_name
                    ):
                        return _snippet(fn_node), fn_node.lineno, fn_node.end_lineno
    else:
        for fn_node in ast.walk(tree):
            if (
                isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and fn_node.name == function_name
            ):
                return _snippet(fn_node), fn_node.lineno, fn_node.end_lineno

    return None


def install_project(checkout_dir: str) -> bool:
    """Try to pip install the project in editable mode. Returns True on success."""
    for setup_file in ["setup.py", "setup.cfg", "pyproject.toml"]:
        if os.path.exists(os.path.join(checkout_dir, setup_file)):
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", ".", "-q",
                 "--no-deps", "--disable-pip-version-check"],
                cwd=checkout_dir, capture_output=True, text=True,
            )
            return result.returncode == 0
    return False


def run_tests_for_bip(
    checkout_dir: str,
    test_file: str,
    timeout: int = 120,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Run the BugsInPy test file in checkout_dir.
    Returns (passing_tests, failing_tests).
    """
    install_project(checkout_dir)

    cmd = [
        sys.executable, "-m", "pytest", "-v", "--tb=short",
        "--no-header", "--disable-warnings", test_file,
    ]
    result = subprocess.run(
        cmd, cwd=checkout_dir, capture_output=True, text=True, timeout=timeout,
    )
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout + result.stderr)

    passing: List[Dict] = []
    failing: List[Dict] = []

    for line in output.splitlines():
        m = re.search(r"(\S+::\S+)\s+(PASSED|FAILED|ERROR)", line)
        if m:
            test_id, status = m.group(1), m.group(2)
            test_name = test_id.split("::")[-1]
            entry = {
                "test_name": test_name,
                "test_function_definition": {"name": test_name, "source": test_id},
                "status": "pass" if status == "PASSED" else "fail",
                "error": None,
            }
            (failing if status in ("FAILED", "ERROR") else passing).append(entry)

    error_lines = re.findall(r"E\s+([A-Za-z0-9_.]+(?:Error|Exception|Warning):.*)", output)
    for test, err in zip(failing, error_lines):
        test["error"] = err.strip()

    return passing, failing


@contextlib.contextmanager
def _patched_source(src_path: str, instrumented_code: str):
    """Replace src_path with instrumented code, restore on exit."""
    with open(src_path) as f:
        original = f.read()
    try:
        with open(src_path, "w") as f:
            f.write(instrumented_code)
        yield
    finally:
        with open(src_path, "w") as f:
            f.write(original)


def run_instrumented_tests(
    checkout_dir: str,
    test_file: str,
    report_path: str,
    timeout: int = 180,
) -> str:
    """Run pytest with CBFL_ENABLED on the checked-out project."""
    semloc_conftest_src = _SRC_ROOT / "conftest.py"
    target_conftest = Path(checkout_dir) / "conftest.py"
    backed_up = False

    if target_conftest.exists():
        shutil.copy2(str(target_conftest), str(target_conftest) + ".bak_semloc")
        backed_up = True

    try:
        shutil.copy2(str(semloc_conftest_src), str(target_conftest))

        env = os.environ.copy()
        env["CBFL_ENABLED"] = "1"
        env["CBFL_REPORT"] = report_path
        semloc_abs = str(_SRC_ROOT.resolve())
        pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = semloc_abs + ((":" + pypath) if pypath else "")

        cmd = [
            sys.executable, "-m", "pytest",
            "--inst", "--cbfl-report", report_path,
            "-v", "--tb=no", "--no-header", "--disable-warnings",
            test_file,
        ]
        subprocess.run(
            cmd, cwd=checkout_dir, capture_output=True, text=True,
            env=env, timeout=timeout,
        )
    finally:
        if backed_up:
            shutil.copy2(str(target_conftest) + ".bak_semloc", str(target_conftest))
            os.remove(str(target_conftest) + ".bak_semloc")
        elif target_conftest.exists():
            os.remove(str(target_conftest))

    return report_path


def run_counterfactual_bip(
    constraints,
    constraint_scores: Dict,
    fn_snippet: str,
    src_path_abs: str,
    full_src: str,
    fn_begin: int,
    checkout_dir: str,
    test_file: str,
    model: str = "claude-sonnet-4-6",
    top_n: int = 5,
    debug: bool = False,
) -> List[Dict]:
    """Run counterfactual verification on top-ranked constraints."""
    from counterfactual import CounterfactualVerifier

    verifier = CounterfactualVerifier(model=model)
    ranked = rank_constraints(constraint_scores)
    c_by_id = {c.cid: c for c in constraints}
    full_lines = full_src.splitlines()

    _, orig_failing = run_tests_for_bip(checkout_dir, test_file)
    orig_failing_set = set(t["test_name"] for t in orig_failing)

    results = []
    for cid, score in ranked[:top_n]:
        if score == 0.0:
            continue
        constraint = c_by_id.get(cid)
        if constraint is None:
            continue

        rel_lines = find_anchor_lines(constraint, fn_snippet)
        rel_anchor = rel_lines[0] if rel_lines else 1
        abs_anchor = fn_begin - 1 + rel_anchor
        buggy_stmt = full_lines[abs_anchor - 1] if 1 <= abs_anchor <= len(full_lines) else ""

        patch = verifier.generate_patch(constraint, buggy_stmt, fn_snippet)
        if patch is None:
            results.append({"cid": cid, "score": score, "status": "Error",
                            "patch": "", "abs_anchor": abs_anchor})
            continue

        patched_full = verifier.apply_patch(full_src, abs_anchor, patch)
        try:
            with _patched_source(src_path_abs, patched_full):
                _, patched_failing = run_tests_for_bip(checkout_dir, test_file)
        except Exception as e:
            results.append({"cid": cid, "score": score, "status": "Error",
                            "patch": patch, "abs_anchor": abs_anchor, "error": str(e)})
            continue

        patched_failing_set = set(t["test_name"] for t in patched_failing)
        still_failing = orig_failing_set & patched_failing_set
        if not orig_failing_set:
            status = "Irrelevant"
        elif not still_failing:
            status = "Primary"
        elif len(still_failing) < len(orig_failing_set):
            status = "Secondary"
        else:
            status = "Irrelevant"

        results.append({
            "cid": cid, "score": score, "status": status,
            "patch": patch, "abs_anchor": abs_anchor,
            "orig_failing": list(orig_failing_set),
            "patched_failing": list(patched_failing_set),
        })
        if debug:
            print(f"[cf] {cid} (score={score:.3f}, line={abs_anchor}): {status}")
        if status == "Primary":
            break

    return results


def run_semloc_on_bip(
    bug_id: str,
    predicted_function: str,
    checkout_dir: str,
    test_file: str,
    model: str = "claude-sonnet-4-6",
    temperature: float = 0.0,
    workdir: Optional[str] = None,
    debug: bool = False,
) -> Dict:
    """
    Run the full SemLoc pipeline on a BugsInPy function.

    Steps:
      1. Locate the function in the checkout
      2. Run tests → passing/failing info
      3. Infer constraints via LLM
      4. Instrument the function
      5. Run instrumented tests → violations
      6. Compute spectrum → ranked lines
      7. Counterfactual verification
    """
    workdir = workdir or f"/tmp/bip_semloc/{bug_id}"
    os.makedirs(workdir, exist_ok=True)

    # 1. Locate function
    class_name, func_name = _parse_qualified_name(predicted_function)

    src_path_rel = None
    # Derive path from the predicted function's module segments
    pred_parts = predicted_function.rstrip("()").split(".")
    for i in range(len(pred_parts) - 1, 0, -1):
        candidate = os.path.join(*pred_parts[:i]) + ".py"
        if os.path.exists(os.path.join(checkout_dir, candidate)):
            src_path_rel = candidate
            break

    if src_path_rel is None:
        return {"error": f"Could not find src_path for {predicted_function}"}

    src_path_abs = os.path.join(checkout_dir, src_path_rel)
    fn_result = find_function_in_file(src_path_abs, func_name, class_name)
    if fn_result is None:
        return {"error": f"Function {func_name!r} not found in {src_path_rel}"}

    fn_snippet, fn_begin, fn_end = fn_result
    if debug:
        print(f"[bip_runner] Found {func_name} at lines {fn_begin}-{fn_end} in {src_path_rel}")

    # 2. Run tests
    with open(src_path_abs) as f:
        full_src = f.read()

    passing, failing = run_tests_for_bip(checkout_dir, test_file)
    if debug:
        print(f"[bip_runner] Tests: {len(passing)} passing, {len(failing)} failing")

    if not failing:
        return {"error": "No failing tests found"}

    MAX_TESTS = 5
    test_results = {
        "target_function": func_name,
        "src_program": [full_src],
        "passing_tests": passing[:MAX_TESTS],
        "failing_tests": failing[:MAX_TESTS],
    }

    # 3. Constraint inference
    if debug:
        print(f"[bip_runner] Inferring constraints with {model} ...")
    try:
        constraints_obj = query_llm_for_constraints(test_results, model=model,
                                                     temperature=temperature)
    except Exception as e:
        return {"error": f"Constraint inference failed: {e}"}

    constraints_path = os.path.join(workdir, f"{func_name}_constraints.json")
    with open(constraints_path, "w") as f:
        json.dump(constraints_obj, f, indent=2)

    _fn_name_parsed, constraints = parse_constraints(json.dumps(constraints_obj))
    if not constraints:
        return {"error": "No constraints generated"}
    if debug:
        print(f"[bip_runner] Generated {len(constraints)} constraints")

    # 4. Instrument the function
    try:
        instrumenter = Instrumenter()
        instrumented_fn = instrumenter.instrument(fn_snippet, json.dumps(constraints_obj))
    except Exception as e:
        return {"error": f"Instrumentation failed: {e}"}

    # Splice instrumented function back into the full source file
    _CBFL_IMPORT = "import cbfl_runtime as _cbfl"
    _CBFL_PRELUDE = _CBFL_IMPORT + "\n\n"
    instrumented_fn_body = (
        instrumented_fn[len(_CBFL_PRELUDE):]
        if instrumented_fn.startswith(_CBFL_PRELUDE)
        else instrumented_fn
    )

    fn_lines = full_src.splitlines()
    before = "\n".join(fn_lines[: fn_begin - 1])
    after = "\n".join(fn_lines[fn_end:])
    instrumented_code = before + "\n" + instrumented_fn_body + "\n" + after

    if _CBFL_IMPORT not in instrumented_code:
        insert_after = 0
        try:
            tree = ast.parse(instrumented_code)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_after = max(insert_after, node.end_lineno)
        except SyntaxError:
            pass
        code_lines = instrumented_code.splitlines()
        code_lines.insert(insert_after, _CBFL_IMPORT)
        instrumented_code = "\n".join(code_lines)

    # 5. Run instrumented tests
    report_path = os.path.join(workdir, "violations.jsonl")
    if os.path.exists(report_path):
        os.remove(report_path)

    try:
        with _patched_source(src_path_abs, instrumented_code):
            run_instrumented_tests(checkout_dir, test_file, report_path)
    except subprocess.TimeoutExpired:
        return {"error": "Instrumented test run timed out"}
    except Exception as e:
        return {"error": f"Instrumented test run failed: {e}"}

    # 6. Compute spectrum
    if not os.path.exists(report_path):
        return {"error": "No violations report generated"}

    try:
        records = load_violations(report_path)
        records = deduplicate_records(records)
        cids = [c.cid for c in constraints]
        matrix = build_matrix(records, cids)
        constraint_scores = score_constraints(matrix)
        stmt_scores = attribute_to_statements(constraint_scores, constraints, fn_snippet)
        ranked = rank_lines(stmt_scores)
    except Exception as e:
        return {"error": f"Spectrum computation failed: {e}"}

    fault_line_raw = constraints_obj.get("fault_line")
    fault_line = None
    if fault_line_raw is not None:
        try:
            fault_line = int(fault_line_raw)
        except (ValueError, TypeError):
            pass

    line_scores = [{"line": ln + fn_begin - 1, "score": sc} for ln, sc in ranked]

    # Compute rank metrics
    best_rank = None
    if fault_line is not None:
        for rank, entry in enumerate(line_scores, 1):
            if entry["line"] == fault_line:
                best_rank = rank
                break
    fn_total_lines = max(fn_end - fn_begin + 1, 1)
    pct_suspicious = round(len(line_scores) / fn_total_lines * 100, 1)

    # 7. Counterfactual verification
    cf_results = []
    try:
        cf_results = run_counterfactual_bip(
            constraints=constraints,
            constraint_scores=constraint_scores,
            fn_snippet=fn_snippet,
            src_path_abs=src_path_abs,
            full_src=full_src,
            fn_begin=fn_begin,
            checkout_dir=checkout_dir,
            test_file=test_file,
            model=model,
            debug=debug,
        )
    except Exception as e:
        if debug:
            print(f"[bip_runner] Counterfactual failed: {e}")

    return {
        "bug_id": bug_id,
        "function": func_name,
        "src_path": src_path_rel,
        "fn_begin": fn_begin,
        "fn_end": fn_end,
        "n_constraints": len(constraints),
        "n_tests_passing": len(passing),
        "n_tests_failing": len(failing),
        "line_scores": line_scores,
        "fault_line": fault_line,
        "best_rank": best_rank,
        "top1": best_rank == 1,
        "top3": best_rank is not None and best_rank <= 3,
        "top5": best_rank is not None and best_rank <= 5,
        "pct_suspicious": pct_suspicious,
        "counterfactual": cf_results,
        "cf_primary": any(r.get("status") == "Primary" for r in cf_results),
        "constraints_path": constraints_path,
        "report_path": report_path,
    }


# ===========================================================================
# CLI
# ===========================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="BugsInPy checkout and SemLoc runner")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- checkout ---
    p_co = sub.add_parser("checkout", help="Checkout a BugsInPy bug at its buggy commit")
    p_co.add_argument("bug_id", help="e.g. pandas_1")
    p_co.add_argument("--workdir", default="/tmp/bip_checkouts")
    p_co.add_argument("--force", action="store_true")
    p_co.add_argument("--faulty-lines", action="store_true", help="Print ground-truth faulty lines from diff")

    # --- run ---
    p_run = sub.add_parser("run", help="Run SemLoc on a checked-out BugsInPy bug")
    p_run.add_argument("bug_id", help="e.g. pandas_1")
    p_run.add_argument("--function", required=True, help="Qualified function name")
    p_run.add_argument("--checkout", required=True, help="Path to checked-out project")
    p_run.add_argument("--test-file", required=True, help="Relative path to test file")
    p_run.add_argument("--out", default=None, help="Output JSON path")
    p_run.add_argument("--model", default="claude-sonnet-4-6")
    p_run.add_argument("--temperature", type=float, default=0.0)
    p_run.add_argument("--debug", action="store_true")

    # --- checkout-and-run ---
    p_car = sub.add_parser("checkout-and-run", help="Checkout then immediately run SemLoc")
    p_car.add_argument("bug_id", help="e.g. pandas_1")
    p_car.add_argument("--function", required=True)
    p_car.add_argument("--workdir", default="/tmp/bip_checkouts")
    p_car.add_argument("--out", default=None)
    p_car.add_argument("--model", default="claude-sonnet-4-6")
    p_car.add_argument("--temperature", type=float, default=0.0)
    p_car.add_argument("--force", action="store_true")
    p_car.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    if args.command == "checkout":
        result = checkout_bug(args.bug_id, workdir=args.workdir, force=args.force)
        print(json.dumps(result, indent=2))
        if args.faulty_lines:
            faulty = get_faulty_lines_from_diff(args.bug_id, result["checkout_dir"])
            print("Faulty lines:", json.dumps(faulty, indent=2))

    elif args.command == "run":
        out = args.out or f"results/RQ3/semloc/{args.bug_id}.json"
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        result = run_semloc_on_bip(
            args.bug_id,
            predicted_function=args.function,
            checkout_dir=args.checkout,
            test_file=args.test_file,
            model=args.model,
            temperature=args.temperature,
            debug=args.debug,
        )
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Lines {result['fn_begin']}-{result['fn_end']}, "
                  f"{result['n_constraints']} constraints")
            for entry in result["line_scores"][:5]:
                print(f"  line {entry['line']:4d}: score={entry['score']:.4f}")
        print(f"Saved to: {out}")

    elif args.command == "checkout-and-run":
        co = checkout_bug(args.bug_id, workdir=args.workdir, force=args.force)
        test_file = co.get("test_file", "")
        if not test_file:
            print("ERROR: No test_file in bug.info; specify with --test-file")
            sys.exit(1)
        out = args.out or f"results/RQ3/semloc/{args.bug_id}.json"
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        result = run_semloc_on_bip(
            args.bug_id,
            predicted_function=args.function,
            checkout_dir=co["checkout_dir"],
            test_file=test_file,
            model=args.model,
            temperature=args.temperature,
            debug=args.debug,
        )
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Done. Top-5 lines:")
            for entry in result["line_scores"][:5]:
                print(f"  line {entry['line']:4d}: score={entry['score']:.4f}")
        print(f"Saved to: {out}")


if __name__ == "__main__":
    main()
