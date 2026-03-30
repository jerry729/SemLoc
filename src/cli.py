#!/usr/bin/env python3
"""
semloc — Command-line interface for the SemLoc fault localization framework.

Sub-commands
------------
  locate  Run the prototype workflow on one program + test file (interactive output).
  run     Run the full batch evaluation pipeline on a working directory.
  report  Print pre-computed result tables (RQ1/RQ2/RQ3).
  demo    Run SemLoc on a bundled benchmark example (batchnorm_running_mean).

Quick start
-----------
  # 1. Configure API keys
  cp config.sh myconfig.sh && nano myconfig.sh
  source myconfig.sh

  # 2. Locate a bug interactively
  semloc locate --program my_func.py --tests test_my_func.py

  # 3. Run full batch pipeline
  semloc run --working-dir my_project/

  # 4. Try the bundled demo (no API key needed)
  semloc demo --skip-llm

  # 5. Print result tables
  semloc report --all
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure src/ is importable regardless of how the CLI is invoked.
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_ARTIFACT_ROOT = _SRC.parent


# ---------------------------------------------------------------------------
# Terminal colour helpers
# ---------------------------------------------------------------------------

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_RED    = "\033[91m"
_YELLOW = "\033[93m"
_GREEN  = "\033[92m"
_CYAN   = "\033[96m"
_WHITE  = "\033[97m"
_BG_RED    = "\033[41m"
_BG_YELLOW = "\033[43m"
_BG_GREEN  = "\033[42m"

def _no_color():
    return not sys.stdout.isatty() or os.environ.get("NO_COLOR")

def _c(code, text):
    return text if _no_color() else f"{code}{text}{_RESET}"

def _header(text):
    width = 72
    print()
    print(_c(_BOLD + _CYAN, "=" * width))
    print(_c(_BOLD + _CYAN, f"  {text}"))
    print(_c(_BOLD + _CYAN, "=" * width))

def _step(n, text):
    print(_c(_BOLD, f"\n[Step {n}] {text}"))
    print(_c(_DIM, "-" * 60))


# ---------------------------------------------------------------------------
# Sub-command: locate  (prototype interactive workflow)
# ---------------------------------------------------------------------------

_LOCATE_STEPS = ["tests", "infer", "instrument", "violations", "matrix", "score", "locate"]

_LOCATE_EPILOG = """\
Steps
-----
  tests        Run the test suite on the buggy program; show pass/fail counts.
  infer        Query the LLM to generate behavioral constraints (cbfl-ir-0.1 JSON).
               Skip with --constraints to load pre-computed constraints instead.
  instrument   Insert runtime __cbfl.check() calls into the program source.
               Output: <out-dir>/instrumented/<func>.py
  violations   Run the instrumented program under pytest; collect violation events.
               Output: <out-dir>/violations/<func>.jsonl
  matrix       Build the test × constraint violation matrix; display it in the terminal.
  score        Compute Ochiai/Tarantula suspiciousness scores; print ranked constraints.
  locate       Attribute constraint scores to source lines; print annotated source.

Workflow examples
-----------------
  # Run all steps at once (default):
  semloc locate --program foo.py --tests test_foo.py --out-dir ./run1

  # Run only the first two steps (tests + infer):
  semloc locate --program foo.py --tests test_foo.py --out-dir ./run1 --steps tests,infer

  # Inspect the inferred constraints, then continue from instrument onward:
  cat ./run1/constraints/foo.json
  semloc locate --program foo.py --tests test_foo.py --out-dir ./run1 \\
      --steps instrument,violations,matrix,score,locate

  # Re-score with a different formula without re-running tests:
  semloc locate --program foo.py --tests test_foo.py --out-dir ./run1 \\
      --steps score,locate --formula tarantula

  # Use pre-computed constraints (no API key needed):
  semloc locate --program foo.py --tests test_foo.py \\
      --constraints my_constraints.json --steps instrument,violations,matrix,score,locate

  # Supply known buggy lines for evaluation:
  semloc locate --program foo.py --tests test_foo.py --ground-truth 42,43

Artifacts saved to --out-dir
-----------------------------
  programs/         copy of the buggy source
  testcases/        copy of the test file
  constraints/      LLM-inferred constraint JSON  (cbfl-ir-0.1 schema)
  instrumented/     program with __cbfl.check() calls injected
  violations/       JSONL violation log per test run
"""


def cmd_locate(argv):
    parser = argparse.ArgumentParser(
        prog="semloc locate",
        description=(
            "Run the SemLoc fault localization prototype on a single program + test file.\n"
            "Each pipeline step can be run individually via --steps so you can inspect\n"
            "intermediate artifacts and resume without restarting from scratch."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_LOCATE_EPILOG,
    )
    parser.add_argument(
        "--program", required=True, metavar="FILE",
        help="Path to the buggy Python source file",
    )
    parser.add_argument(
        "--tests", required=True, metavar="FILE",
        help="Path to the pytest test file",
    )
    parser.add_argument(
        "--out-dir", metavar="DIR",
        help="Directory for all intermediate artifacts.  Re-use the same directory\n"
             "across --steps invocations to resume the pipeline without re-running\n"
             "earlier steps.  A temporary directory is used when not specified.",
    )
    parser.add_argument(
        "--steps",
        default=",".join(_LOCATE_STEPS),
        metavar="STEP[,STEP…]",
        help=(
            "Comma-separated list of steps to execute.  Steps not listed are skipped\n"
            "and their outputs are loaded from --out-dir instead.\n"
            f"Available steps: {', '.join(_LOCATE_STEPS)}\n"
            "(default: all steps)"
        ),
    )
    parser.add_argument(
        "--constraints", metavar="FILE",
        help="Pre-computed constraints JSON — automatically skips the 'infer' step.\n"
             "Useful for benchmarks or when you already have constraints on disk.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        metavar="MODEL",
        help=(
            "LLM model for the 'infer' step.  The model name selects the backend:\n"
            "\n"
            "  claude-*   → Anthropic on Vertex AI\n"
            "               Requires: ANTHROPIC_VERTEX_PROJECT_ID, CLOUD_ML_REGION\n"
            "               (or application-default credentials via `gcloud auth`)\n"
            "\n"
            "  gemini-*   → Google Gemini API\n"
            "               Requires: GEMINI_API_KEY\n"
            "\n"
            "  gpt-* / o* → OpenAI API\n"
            "               Requires: OPENAI_API_KEY\n"
            "\n"
            "Examples: --model claude-sonnet-4-6\n"
            "          --model gemini-2.5-pro\n"
            "          --model gpt-4o\n"
            "\n"
            "Default: $CLAUDE_MODEL env var, or claude-sonnet-4-6"
        ),
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0,
        metavar="T",
        help="LLM sampling temperature for the 'infer' step (default: 0.0)",
    )
    parser.add_argument(
        "--formula", choices=["ochiai", "tarantula"], default="ochiai",
        help="Suspiciousness formula for the 'score' and 'locate' steps (default: ochiai)",
    )
    parser.add_argument(
        "--top", type=int, default=10,
        metavar="N",
        help="Number of top-suspicious lines shown in the annotated source (default: 10)",
    )
    parser.add_argument(
        "--ground-truth", metavar="LINES",
        help="Comma-separated ground-truth faulty line numbers, e.g. '42,43'.\n"
             "Auto-detected from benchmark/ground_truth.json when omitted.",
    )
    args = parser.parse_args(argv)

    # Parse and validate --steps
    requested = [s.strip() for s in args.steps.split(",") if s.strip()]
    unknown = [s for s in requested if s not in _LOCATE_STEPS]
    if unknown:
        parser.error(f"Unknown step(s): {', '.join(unknown)}. "
                     f"Available: {', '.join(_LOCATE_STEPS)}")
    steps = set(requested)

    def _run(name):
        return name in steps

    program_path = Path(args.program).resolve()
    tests_path   = Path(args.tests).resolve()

    if not program_path.exists():
        parser.error(f"program file not found: {program_path}")
    if not tests_path.exists():
        parser.error(f"test file not found: {tests_path}")

    import re as _re
    import shutil, tempfile, json, subprocess
    from instrumentation import Instrumenter, parse_constraints
    from constraint_inference import query_llm_for_constraints
    from spectrum import (
        load_violations, deduplicate_records, group_by_sut,
        build_matrix, score_constraints, attribute_to_statements,
        rank_constraints, rank_lines,
    )

    func_name = program_path.stem

    # Working directory — persistent across --steps invocations.
    # Always resolve to absolute so subprocess calls work regardless of cwd.
    if args.out_dir:
        wd = Path(args.out_dir).resolve()
        wd.mkdir(parents=True, exist_ok=True)
    else:
        wd = Path(tempfile.mkdtemp(prefix=f"semloc_{func_name}_")).resolve()

    programs_dir   = wd / "programs"
    testcases_dir  = wd / "testcases"
    constraints_dir = wd / "constraints"
    inst_dir       = wd / "instrumented"
    violations_dir = wd / "violations"

    for d in [programs_dir, testcases_dir, constraints_dir, inst_dir, violations_dir]:
        d.mkdir(exist_ok=True)

    shutil.copy(program_path, programs_dir / program_path.name)
    shutil.copy(tests_path,   testcases_dir / tests_path.name)
    src = program_path.read_text()

    # Ground truth: explicit flag > benchmark GT file > none
    gt_lines: list[int] = []
    if args.ground_truth:
        try:
            gt_lines = [int(x.strip()) for x in args.ground_truth.split(",") if x.strip()]
        except ValueError:
            print(f"Warning: could not parse --ground-truth '{args.ground_truth}'",
                  file=sys.stderr)
    else:
        gt_path = _ARTIFACT_ROOT / "benchmark" / "ground_truth.json"
        if gt_path.exists():
            for entry in json.loads(gt_path.read_text()).get("programs", []):
                if entry.get("file", "").replace(".py", "") == func_name:
                    gt_lines = entry.get("faulty_lines", [])
                    break

    running_all = (steps == set(_LOCATE_STEPS))
    step_list_str = ", ".join(sorted(steps, key=_LOCATE_STEPS.index))

    _header(f"SemLoc  ·  {func_name}")
    print(f"  Program : {program_path}")
    print(f"  Tests   : {tests_path}")
    print(f"  Steps   : {step_list_str}" + ("  (all)" if running_all else ""))
    print(f"  Model   : {args.model}  (T={args.temperature})")
    print(f"  WorkDir : {wd}")
    if not running_all:
        print(_c(_DIM, f"  Tip: reuse --out-dir {wd} to continue with remaining steps."))

    # ------------------------------------------------------------------
    # Step 1 — run tests  (gate: "tests")
    # ------------------------------------------------------------------
    # Test files use `if pytest.inst:` which requires the conftest plugin.
    # Run with `-p conftest` (no --inst) from `wd` so that the test file's
    # own sys.path.insert resolves `from programs.<func> import ...` correctly.
    passing_tests: list[str] = []
    failing_tests: list[str] = []

    _step(1, "Run tests  [tests]" if _run("tests") else "Run tests  [tests]  — SKIPPED")

    if _run("tests"):
        env1 = os.environ.copy()
        env1["PYTHONPATH"] = str(_SRC) + ":" + env1.get("PYTHONPATH", "")

        r1 = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "--tb=no",
             "-p", "conftest",
             str(testcases_dir / f"test_{func_name}.py")],
            env=env1, capture_output=True, text=True, cwd=str(wd),
        )
        out1 = _re.sub(r"\x1b\[[0-9;]*m", "", r1.stdout)
        for line in out1.splitlines():
            m = _re.search(r"::([^\s]+)\s+(PASSED|FAILED)", line)
            if m:
                name, st = m.group(1), m.group(2)
                (passing_tests if st == "PASSED" else failing_tests).append(name)

        n_pass, n_fail = len(passing_tests), len(failing_tests)
        if n_pass == 0 and n_fail == 0:
            print(_c(_RED, "  Could not collect any tests. Pytest output:"))
            print(out1[-600:])
            sys.exit(1)

        status = (_c(_GREEN, f"PASS×{n_pass}") if n_pass else "") + \
                 ("  " if n_pass and n_fail else "") + \
                 (_c(_RED, f"FAIL×{n_fail}") if n_fail else "")
        print(f"  Tests:  {status}")
        if n_fail == 0:
            print(_c(_YELLOW,
                     "  Warning: no failing tests — SemLoc needs at least one failure."))
        # Save for resume
        (wd / "tests.json").write_text(json.dumps(
            {"passing": passing_tests, "failing": failing_tests}))
    else:
        saved = wd / "tests.json"
        if saved.exists():
            d = json.loads(saved.read_text())
            passing_tests, failing_tests = d["passing"], d["failing"]
            print(f"  Loaded from disk — "
                  f"{_c(_GREEN, f'PASS×{len(passing_tests)}')}  "
                  f"{_c(_RED, f'FAIL×{len(failing_tests)}')}")
        else:
            print(_c(_DIM, "  (no saved test results — run 'tests' step first)"))

    tr = {
        "target_function": func_name,
        "passing_tests":  [{"test_name": t} for t in passing_tests],
        "failing_tests":  [{"test_name": t} for t in failing_tests],
        "src_program": [src],
    }

    # ------------------------------------------------------------------
    # Step 2 — infer constraints  (gate: "infer")
    # ------------------------------------------------------------------
    constraints_path = constraints_dir / f"{func_name}.json"

    if args.constraints:
        # --constraints always copies, regardless of --steps
        _step(2, "Load pre-computed constraints  [infer]  — via --constraints")
        shutil.copy(args.constraints, constraints_path)
    elif _run("infer"):
        _step(2, f"Infer constraints via LLM  [infer]  ({args.model})")
        model = args.model
        if model.startswith("claude"):
            needed = "ANTHROPIC_VERTEX_PROJECT_ID + CLOUD_ML_REGION (Vertex AI)"
            key_ok = bool(os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID"))
        elif model.startswith("gemini"):
            needed = "GEMINI_API_KEY"
            key_ok = bool(os.environ.get("GEMINI_API_KEY"))
        else:
            needed = "OPENAI_API_KEY"
            key_ok = bool(os.environ.get("OPENAI_API_KEY"))
        if not key_ok:
            print(_c(_YELLOW, f"  WARNING: {needed} not set — API call will likely fail."))
            print(_c(_DIM,    f"  Set the env var or use --constraints to skip LLM."))
        result = query_llm_for_constraints(tr, model=model, temperature=args.temperature)
        raw = result if isinstance(result, str) else json.dumps(result, indent=2)
        constraints_path.write_text(raw)
    else:
        _step(2, "Infer constraints  [infer]  — SKIPPED")

    if constraints_path.exists():
        constraint_json   = json.loads(constraints_path.read_text())
        constraints_list  = constraint_json.get("constraints", [])
        action = "Loaded" if not _run("infer") or args.constraints else "Inferred"
        print(f"  {action} {len(constraints_list)} constraint(s)  "
              f"{_c(_DIM, f'→ {constraints_path}')}")
        for c in constraints_list:
            cid      = c.get("id", "?")
            category = c.get("category", "?")
            region   = c.get("instrument", {}).get("region", "?")
            expr     = c.get("spec", {}).get("expr", "?")
            print(f"    {_c(_CYAN, cid):12s}  [{category} / {region}]  {expr}")
    else:
        print(_c(_DIM, f"  (no constraints file — run 'infer' step or pass --constraints)"))

    # ------------------------------------------------------------------
    # Step 3 — instrument  (gate: "instrument")
    # ------------------------------------------------------------------
    inst_path = inst_dir / f"{func_name}.py"

    _step(3, "Instrument program  [instrument]" if _run("instrument")
             else "Instrument program  [instrument]  — SKIPPED")

    if _run("instrument"):
        if not constraints_path.exists():
            print(_c(_RED, "  Cannot instrument: no constraints file. "
                           "Run 'infer' step first."))
            sys.exit(1)
        try:
            instrumented = Instrumenter().instrument(src, constraints_path.read_text())
            inst_path.write_text(instrumented)
            n_checks = instrumented.count("_cbfl.check(")
            print(f"  Inserted {n_checks} runtime check(s)  "
                  f"{_c(_DIM, f'→ {inst_path}')}")
        except Exception as e:
            print(_c(_RED, f"  Instrumentation failed: {e}"))
            sys.exit(1)
    elif inst_path.exists():
        n_checks = inst_path.read_text().count("_cbfl.check(")
        print(f"  Loaded from disk — {n_checks} check(s)  {_c(_DIM, f'→ {inst_path}')}")
    else:
        print(_c(_DIM, "  (no instrumented file — run 'instrument' step first)"))

    # ------------------------------------------------------------------
    # Step 4 — collect violations  (gate: "violations")
    # ------------------------------------------------------------------
    violations_path = violations_dir / f"{func_name}.jsonl"

    _step(4, "Collect violations  [violations]" if _run("violations")
             else "Collect violations  [violations]  — SKIPPED")

    if _run("violations"):
        if not inst_path.exists():
            print(_c(_RED, "  Cannot collect violations: no instrumented file. "
                           "Run 'instrument' step first."))
            sys.exit(1)
        if violations_path.exists():
            violations_path.unlink()

        env4 = os.environ.copy()
        env4["PYTHONPATH"] = (
            str(inst_dir) + ":" + str(_SRC) +
            (":" + env4.get("PYTHONPATH", "") if env4.get("PYTHONPATH") else "")
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-p", "conftest", "--inst",
             f"--cbfl-report={violations_path}", "-q", "--tb=no",
             str(testcases_dir / f"test_{func_name}.py")],
            env=env4, capture_output=True, text=True, cwd=str(wd),
        )
        if not violations_path.exists():
            print(_c(_RED, "  No violations file written — instrumented tests may have crashed."))
            print(result.stderr[-800:] if result.stderr else "")
            sys.exit(1)

    if violations_path.exists():
        records = deduplicate_records(load_violations(str(violations_path)))
        n_violations = sum(len(r.violations) for r in records)
        n_tests = len(records)
        action = "Collected" if _run("violations") else "Loaded from disk —"
        print(f"  {action} {n_violations} violation event(s) across {n_tests} test(s)  "
              f"{_c(_DIM, f'→ {violations_path}')}")
    else:
        records = []
        print(_c(_DIM, "  (no violations file — run 'violations' step first)"))

    # ------------------------------------------------------------------
    # Step 5 — violation matrix  (gate: "matrix")
    # ------------------------------------------------------------------
    _step(5, "Build violation matrix  [matrix]" if _run("matrix")
             else "Build violation matrix  [matrix]  — SKIPPED")

    vm = parsed_constraints = None
    if records and constraints_path.exists():
        _, parsed_constraints = parse_constraints(constraints_path.read_text())
        cids = [c.cid for c in parsed_constraints]
        sut_records = group_by_sut(records).get(func_name, records)
        vm = build_matrix(sut_records, cids, sut=func_name)
        if _run("matrix"):
            _print_violation_matrix(vm, cids)
        else:
            print(f"  {len(vm.passing)} passing / {len(vm.failing)} failing  ·  "
                  f"{len(cids)} constraint(s)  (display skipped)")
    else:
        print(_c(_DIM, "  (need violations + constraints — run earlier steps first)"))

    # ------------------------------------------------------------------
    # Step 6 — score  (gate: "score")
    # ------------------------------------------------------------------
    _step(6, f"Score constraints  [score]  (formula: {args.formula})" if _run("score")
             else f"Score constraints  [score]  — SKIPPED")

    constraint_scores = ranked_cs = None
    if vm is not None and parsed_constraints is not None:
        constraint_scores = score_constraints(vm)
        ranked_cs = rank_constraints(constraint_scores, formula=args.formula)
        if _run("score"):
            _print_constraint_scores(ranked_cs, constraint_scores, parsed_constraints)
        else:
            top_cid, top_score = ranked_cs[0] if ranked_cs else ("?", 0)
            print(f"  Top constraint: {_c(_CYAN, top_cid)}  score={top_score:.3f}  "
                  f"(display skipped)")
    else:
        print(_c(_DIM, "  (need violation matrix — run earlier steps first)"))

    # ------------------------------------------------------------------
    # Step 7 — locate  (gate: "locate")
    # ------------------------------------------------------------------
    _step(7, "Attribute scores to source lines  [locate]" if _run("locate")
             else "Attribute scores to source lines  [locate]  — SKIPPED")

    ranked_lines: list = []
    line_scores: dict  = {}
    if constraint_scores is not None and parsed_constraints is not None:
        line_scores  = attribute_to_statements(
            constraint_scores, parsed_constraints, src, formula=args.formula)
        ranked_lines = rank_lines(line_scores)
        if _run("locate"):
            _print_annotated_source(src, line_scores, ranked_lines,
                                    top=args.top, func_name=func_name, gt_lines=gt_lines)
        else:
            top_ln, top_sc = ranked_lines[0] if ranked_lines else (None, 0)
            print(f"  Top line: {top_ln}  score={top_sc:.3f}  (display skipped)")
    else:
        print(_c(_DIM, "  (need scores — run earlier steps first)"))

    # ------------------------------------------------------------------
    # Summary  (shown whenever at least 'locate' data is available)
    # ------------------------------------------------------------------
    _header("Result Summary")
    src_lines_list = src.splitlines()

    if ranked_lines:
        gt_set = set(gt_lines)
        print(f"  Top suspicious lines ({args.formula}):")
        for rank, (ln, score) in enumerate(ranked_lines[:args.top], 1):
            bar   = _score_bar(score)
            snip  = src_lines_list[ln - 1].strip() if 0 < ln <= len(src_lines_list) else ""
            gt_marker = _c(_GREEN, " ← FAULT") if ln in gt_set else ""
            print(f"    #{rank:<3d} line {ln:>4d}  {bar}  {score:.3f}  "
                  f"{_c(_DIM, snip[:55])}{gt_marker}")
    else:
        print(_c(_YELLOW, "  No suspicious lines found — run all steps to see results."))

    if gt_lines and ranked_lines:
        _print_gt_evaluation(ranked_lines, gt_lines, src_lines_list)

    print()
    print(f"  Artifacts saved to: {wd}")
    if not running_all:
        remaining = [s for s in _LOCATE_STEPS if s not in steps]
        if remaining:
            print(_c(_DIM, f"  Remaining steps: {', '.join(remaining)}"))
            print(_c(_DIM, f"  Resume with:  semloc locate --program {args.program} "
                          f"--tests {args.tests} --out-dir {wd} "
                          f"--steps {','.join(remaining)}"))
    print()


# ---------------------------------------------------------------------------
# Display helpers for locate
# ---------------------------------------------------------------------------

def _print_violation_matrix(vm, cids):
    """Print a compact test × constraint violation matrix."""
    MAX_COLS = 18  # truncate very wide constraint lists
    display_cids = cids[:MAX_COLS]
    truncated = len(cids) > MAX_COLS

    col_w = max(4, max((len(c) for c in display_cids), default=4))
    hdr = "  {:<30s}  {}  {}".format(
        "Test", " ".join(f"{c:>{col_w}}" for c in display_cids),
        "…" if truncated else "",
    )
    print(_c(_DIM, hdr))
    print(_c(_DIM, "  " + "-" * (len(hdr) - 2)))

    for i, rec in enumerate(vm.records):
        outcome_color = _GREEN if rec.outcome == "passed" else _RED
        marker = _c(outcome_color, "P" if rec.outcome == "passed" else "F")
        short_id = rec.nodeid.split("::")[-1][:28]
        cells = []
        for j, cid in enumerate(display_cids):
            violated = vm.matrix[i][j] if j < len(vm.matrix[i]) else False
            if violated:
                cells.append(_c(_RED, f"{'✗':>{col_w}}"))
            else:
                cells.append(_c(_DIM, f"{'·':>{col_w}}"))
        row = "  [{marker}] {id:<28s}  {cells}".format(
            marker=marker, id=short_id, cells=" ".join(cells)
        )
        print(row)

    print()
    print(f"  {len(vm.passing)} passing  /  {len(vm.failing)} failing  ·  "
          f"{len(cids)} constraint(s)" + (f"  (showing first {MAX_COLS})" if truncated else ""))


def _print_constraint_scores(ranked_cs, scores, parsed_constraints):
    """Print a ranked table of constraint suspiciousness scores."""
    c_meta = {c.cid: c for c in parsed_constraints}
    print(f"  {'Rank':<5} {'CID':<8} {'Score':>7}  {'ef':>4} {'ep':>4}  {'Region':<14}  Spec")
    print(_c(_DIM, "  " + "-" * 72))
    for rank, (cid, score) in enumerate(ranked_cs, 1):
        s   = scores.get(cid, {})
        ef  = s.get("ef", 0)
        ep  = s.get("ep", 0)
        c   = c_meta.get(cid)
        region = c.region if c else "?"
        expr   = (c.spec.get("expr", "") if c else "")[:40]
        score_color = _RED if score > 0.5 else (_YELLOW if score > 0.2 else _DIM)
        print(f"  {rank:<5} {_c(_CYAN, cid):<8}  {_c(score_color, f'{score:.3f}'):>7}  "
              f"{ef:>4} {ep:>4}  {region:<14}  {_c(_DIM, expr)}")


def _score_bar(score, width=10):
    filled = round(score * width)
    bar = "█" * filled + "░" * (width - filled)
    color = _RED if score > 0.5 else (_YELLOW if score > 0.2 else _DIM)
    return _c(color, bar)


def _print_annotated_source(src, line_scores, ranked_lines, top, func_name, gt_lines=None):
    """Print source with suspicious lines highlighted and score annotations.

    Top-ranked lines are highlighted in red/yellow.
    Ground-truth faulty lines are marked with a green ★ marker.
    Lines that are both top-ranked AND ground truth get a combined display.
    """
    gt_set = set(gt_lines or [])
    top_lines = {ln for ln, _ in ranked_lines[:top]}
    any_scored = bool(line_scores)
    lines = src.splitlines()
    max_score = ranked_lines[0][1] if ranked_lines else 1.0

    legend = []
    if any_scored:
        legend.append(f"top-{top} suspicious lines highlighted")
    if gt_set:
        legend.append(_c(_GREEN, "★") + " = ground-truth fault")
    legend_str = "  (" + ",  ".join(legend) + ")" if legend else ""

    print(f"\n  {_c(_BOLD, func_name + '.py')}{legend_str}\n")

    for i, line in enumerate(lines, 1):
        score    = line_scores.get(i, 0.0)
        is_top   = i in top_lines
        is_fault = i in gt_set

        gt_marker = _c(_GREEN + _BOLD, " ★") if is_fault else "  "

        if is_top:
            bar   = _score_bar(score / max_score if max_score else 0)
            rank  = next(r for r, (ln, _) in enumerate(ranked_lines[:top], 1) if ln == i)
            color = _BG_RED if score == max_score else _BG_YELLOW
            print(f"  {_c(_BOLD, f'{i:4d}')}: {_c(color, line):<60}"
                  f"  {bar} {_c(_BOLD, f'{score:.3f}')}  #{rank}{gt_marker}")
        elif is_fault:
            # Ground-truth line not in the top-N — show it dimly with GT marker
            print(f"  {_c(_BOLD, f'{i:4d}')}: {_c(_DIM, line):<60}"
                  f"  {'':14}      {gt_marker}")
        else:
            print(_c(_DIM, f"  {i:4d}: {line}"))


def _print_gt_evaluation(ranked_lines, gt_lines, src_lines_list):
    """Print a ground-truth evaluation block: rank of each faulty line and Acc@k."""
    gt_set = set(gt_lines)
    ranked_line_nums = [ln for ln, _ in ranked_lines]

    print()
    print(_c(_BOLD, "  Ground-Truth Evaluation"))
    print(_c(_DIM,  "  " + "-" * 50))

    # Per-fault-line rank
    for gl in sorted(gt_lines):
        snip = src_lines_list[gl - 1].strip() if 0 < gl <= len(src_lines_list) else ""
        if gl in ranked_line_nums:
            rank = ranked_line_nums.index(gl) + 1
            bar  = _score_bar(ranked_lines[rank - 1][1])
            rank_str = _c(_GREEN if rank <= 3 else _YELLOW, f"rank #{rank}")
        else:
            rank_str = _c(_RED, "not ranked")
            bar = _score_bar(0)
        print(f"    line {gl:>4d}  {rank_str:<20}  {bar}  {_c(_DIM, snip[:45])}")

    # Acc@k
    print()
    for k in (1, 3, 5):
        top_k = set(ranked_line_nums[:k])
        hit   = bool(top_k & gt_set)
        tick  = _c(_GREEN, "✔") if hit else _c(_RED, "✘")
        print(f"    Acc@{k}  {tick}  ({'fault in top-' + str(k) if hit else 'fault not in top-' + str(k)})")
    print()


# ---------------------------------------------------------------------------
# Sub-command: run
# ---------------------------------------------------------------------------

def cmd_run(argv):
    """Delegate to run_eval.main() with the given argv."""
    sys.argv = ["semloc run"] + argv
    import run_eval
    run_eval.main()


# ---------------------------------------------------------------------------
# Sub-command: report
# ---------------------------------------------------------------------------

def cmd_report(argv):
    """Delegate to print_results main() with the given argv."""
    root = str(_ARTIFACT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    sys.argv = ["semloc report"] + argv
    import print_results
    print_results.main()


# ---------------------------------------------------------------------------
# Sub-command: demo
# ---------------------------------------------------------------------------

_DEMO_PROGRAMS = ["batchnorm_running_mean", "blend_levels", "api_rate_guard", "ad_mix"]

def cmd_demo(argv):
    """Run the prototype workflow on a bundled benchmark example."""
    parser = argparse.ArgumentParser(
        prog="semloc demo",
        description="Run SemLoc on a bundled benchmark example using the interactive locate workflow.",
    )
    parser.add_argument(
        "--program", default="batchnorm_running_mean", choices=_DEMO_PROGRAMS,
        help="Which bundled example to run (default: batchnorm_running_mean)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        help="LLM model (default: $CLAUDE_MODEL or claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--skip-llm", action="store_true", default=False,
        help="Use pre-computed constraints (no API key needed)",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0,
        help="LLM temperature (default: 0.0)",
    )
    parser.add_argument(
        "--top", type=int, default=5,
        help="Number of top suspicious lines to show (default: 5)",
    )
    args = parser.parse_args(argv)

    benchmark = _ARTIFACT_ROOT / "benchmark"
    program_file  = benchmark / "programs"  / f"{args.program}.py"
    tests_file    = benchmark / "testcases" / f"test_{args.program}.py"

    if not program_file.exists():
        print(f"[demo] Program not found: {program_file}", file=sys.stderr)
        sys.exit(1)
    if not tests_file.exists():
        print(f"[demo] Test file not found: {tests_file}", file=sys.stderr)
        sys.exit(1)

    locate_argv = [
        "--program",     str(program_file),
        "--tests",       str(tests_file),
        "--model",       args.model,
        "--temperature", str(args.temperature),
        "--top",         str(args.top),
    ]

    if args.skip_llm:
        # Find pre-computed constraints
        constraints_candidates = [
            _ARTIFACT_ROOT / "results" / "RQ2" / "claude_T0.8" / "constraints" / f"{args.program}.json",
        ]
        found = next((p for p in constraints_candidates if p.exists()), None)
        if found:
            locate_argv += ["--constraints", str(found)]
            print(f"[demo] Using pre-computed constraints: {found}")
        else:
            print(f"[demo] Warning: no pre-computed constraints for '{args.program}'; "
                  "LLM inference will run.", file=sys.stderr)

    cmd_locate(locate_argv)


# ---------------------------------------------------------------------------
# Top-level dispatcher
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="semloc",
        description="SemLoc — semantic constraint-based fault localization.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version="semloc 1.0.0")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    subparsers.add_parser(
        "locate",
        help="Run the prototype workflow on a single program + test file.",
        add_help=False,
    )
    subparsers.add_parser(
        "run",
        help="Run the full batch evaluation pipeline on a working directory.",
        add_help=False,
    )
    subparsers.add_parser(
        "report",
        help="Print pre-computed result tables (RQ1/RQ2/RQ3).",
        add_help=False,
    )
    subparsers.add_parser(
        "demo",
        help="Run SemLoc on a bundled benchmark example.",
        add_help=False,
    )

    args, remaining = parser.parse_known_args()

    if args.command == "locate":
        cmd_locate(remaining)
    elif args.command == "run":
        cmd_run(remaining)
    elif args.command == "report":
        cmd_report(remaining)
    elif args.command == "demo":
        cmd_demo(remaining)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
