#!/usr/bin/env python3
"""
run_eval.py — End-to-end SemLoc evaluation pipeline.

Steps:
  1. Run tests on buggy programs; save execution results to execution/
  2. Build LLM prompts (with SSA) from execution results; save to prompts/
  3. Query LLM for constraints; save to constraints/
  4. Instrument programs with constraints; save to instrumented/
  5. Run instrumented tests and collect violations; save to violations/
  6. Compute spectrum (violation matrix + Ochiai scores); save to scores/
  7. Counterfactual verification of top-ranked constraints; save to refined/
  8. Report metrics (suspicious-line %, top line, primary constraint)
  3b. Re-infer constraints (CF disabled): save to constraints_refined/
      Then re-runs 4b→5b→6b on merged constraints.

Usage:
  python run_eval.py [--working-dir example_batch]
  python run_eval.py --skip-llm --skip-counterfactual   # use existing constraints
  python run_eval.py --steps 6,7,8                       # resume from step 6
"""

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from instrumentation import Instrumenter, parse_constraints
from constraint_inference import (
    run_pytest,
    build_prompt_for_all_python,
    query_llm_for_constraints,
)
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


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------


def step1_run_tests(working_dir: str, force: bool = False) -> None:
    """Run pytest on all test files; save execution JSON to execution/."""
    exec_dir = os.path.join(working_dir, "execution")
    os.makedirs(exec_dir, exist_ok=True)

    results = run_pytest(
        test_dir=os.path.join(working_dir, "testcases"),
        test_file=None,
        json_dir=os.path.join(working_dir, "json_testcases"),
        src_dir=os.path.join(working_dir, "programs"),
    )
    for tr in results:
        func_name = tr["target_function"]
        save_path = os.path.join(exec_dir, f"{func_name}.json")
        if not force and os.path.exists(save_path):
            print(f"[step1] Skip {func_name} (exists)")
            continue
        with open(save_path, "w") as f:
            json.dump(tr, f, indent=2)
        print(f"[step1] Saved {save_path}")


def _extract_fn_with_linenos(src_text: str, fn_name: str) -> str:
    """Return the target function source with 1-indexed file line numbers prefixed."""
    import ast as _ast
    try:
        tree = _ast.parse(src_text)
    except SyntaxError:
        return src_text
    src_lines = src_text.splitlines()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.FunctionDef) and node.name == fn_name:
            fn_lines = src_lines[node.lineno - 1 : node.end_lineno]
            return "\n".join(
                f"{node.lineno + i:4d}: {line}" for i, line in enumerate(fn_lines)
            )
    return src_text


def step2_build_prompts(working_dir: str, force: bool = False) -> None:
    """Build LLM prompts (including SSA form) from execution results; save SSA to ssa/."""
    prompts_dir = os.path.join(working_dir, "prompts")
    exec_dir = os.path.join(working_dir, "execution")
    ssa_dir = os.path.join(working_dir, "ssa")
    os.makedirs(prompts_dir, exist_ok=True)
    os.makedirs(ssa_dir, exist_ok=True)

    from constraint_inference import _build_ssa_for
    from prompt_template import build_llm_prompt

    for json_file in sorted(Path(exec_dir).glob("*.json")):
        func_name = json_file.stem
        prompt_path = os.path.join(prompts_dir, f"{func_name}.txt")
        ssa_path = os.path.join(ssa_dir, f"{func_name}.py")

        if not force and os.path.exists(prompt_path):
            continue

        with open(json_file) as f:
            t = json.load(f)

        src_text = t["src_program"][0] if isinstance(t.get("src_program"), list) else t.get("src_program", "")
        program_code = _extract_fn_with_linenos(src_text, func_name)

        ssa_code, def_map = _build_ssa_for(t.get("src_program", []), func_name)

        # Save SSA form to disk
        if ssa_code:
            with open(ssa_path, "w") as f:
                f.write(ssa_code)

        p = build_llm_prompt(
            program_code,
            t["passing_tests"],
            t["failing_tests"],
            ssa_code=ssa_code,
            def_map=def_map,
        )
        with open(prompt_path, "w") as f:
            f.write(p)

    print(f"[step2] Prompts written to {prompts_dir}")
    print(f"[step2] SSA forms written to {ssa_dir}")


def step3_query_llm(working_dir: str, force: bool = False, model: str = "gpt-4o",
                    temperature: float = 0.0,
                    exec_dir_override: Optional[str] = None,
                    workers: int = 8) -> None:
    """Query LLM for constraints; save cbfl-ir-0.1 JSON to constraints/."""
    import concurrent.futures

    exec_dir = exec_dir_override or os.path.join(working_dir, "execution")
    constraints_dir = os.path.join(working_dir, "constraints")
    os.makedirs(constraints_dir, exist_ok=True)

    json_files = sorted(Path(exec_dir).glob("*.json"))

    def _do_one(json_file):
        func_name = json_file.stem
        out_path = os.path.join(constraints_dir, f"{func_name}.json")
        if not force and os.path.exists(out_path):
            print(f"[step3] Skip {func_name} (constraints exist)")
            return
        with open(json_file) as f:
            test_results = json.load(f)
        print(f"[step3] Querying LLM for {func_name} (model={model}, T={temperature})…")
        try:
            constraints = query_llm_for_constraints(test_results, model=model,
                                                    temperature=temperature)
            with open(out_path, "w") as f:
                json.dump(constraints, f, indent=2)
            print(f"[step3] Saved {out_path}")
        except Exception as e:
            print(f"[step3] ERROR for {func_name}: {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(_do_one, json_files))


_REGION_TO_CATEGORY = {
    "ENTRY": "PRECONDITION",
    "ANY_RETURN": "POSTCONDITION",
    "EXIT": "POSTCONDITION",
    "LOOP_HEAD": "INVARIANT_LOOP",
    "LOOP_TAIL": "INVARIANT_LOOP",
    "AFTER_DEF": "VALUE_RANGE",
    "BEFORE_USE": "VALUE_RANGE",
    "AFTER_CALL": "RELATION",
    "ON_EXIT": "TEMPORAL_CALL_SNAPSHOT",
}


def _normalize_constraints_to_cbfl_ir(ir_obj: dict) -> None:
    """Normalize LLM output to cbfl-ir-0.1 schema in-place.

    Handles two common deviation patterns:
    1. Flat schema: top-level 'region'/'anchor'/'expr' instead of
       nested 'instrument.region'/'instrument.anchor'/'spec.expr'
    2. Missing 'category': inferred from region or defaulted to RELATION
    """
    for c in ir_obj.get("constraints", []):
        # --- Fix nested instrument/spec structure ---
        if "instrument" not in c:
            region = c.pop("region", None)
            anchor = c.pop("anchor", {})
            c["instrument"] = {"region": region, "anchor": anchor or {}}
        if "spec" not in c:
            expr = c.pop("expr", None)
            if expr is not None:
                c["spec"] = {"expr": expr}
            else:
                c["spec"] = {}
        # --- Fix missing category ---
        if not c.get("category"):
            region = (c.get("instrument") or {}).get("region", "")
            c["category"] = _REGION_TO_CATEGORY.get(region, "RELATION")


def step3b_iterative_refine(working_dir: str, force: bool = False,
                             model: str = "gemini-2.5-pro",
                             temperature: float = 0.0,
                             workers: int = 8,
                             exec_dir_override: Optional[str] = None) -> None:
    """Re-infer constraints using violation evidence from round 1 (CF disabled path).

    Reads:  execution/<fn>.json  (original test results)
            scores/<fn>.json     (round-1 spectrum scores)
            violations/<fn>.jsonl
            constraints/<fn>.json
    Writes: constraints_refined/<fn>.json  (complementary new constraints only)
            constraints_merged/<fn>.json   (original + refined combined)
    """
    import concurrent.futures
    from prompt_template import build_refinement_prompt
    from constraint_inference import query_llm_for_constraints, _build_ssa_for

    exec_dir      = exec_dir_override or os.path.join(working_dir, "execution")
    scores_dir    = os.path.join(working_dir, "scores")
    viols_dir     = os.path.join(working_dir, "violations")
    c_dir         = os.path.join(working_dir, "constraints")
    refined_dir   = os.path.join(working_dir, "constraints_refined")
    merged_dir    = os.path.join(working_dir, "constraints_merged")
    os.makedirs(refined_dir, exist_ok=True)
    os.makedirs(merged_dir,  exist_ok=True)

    exec_files = sorted(Path(exec_dir).glob("*.json"))

    def _classify_constraints(scores: dict, orig_constraints: list):
        """Split constraints into discriminative / over-approx / silent."""
        score_map = {}
        for cid, s in scores.items():
            ef = s.get("ef", 0)
            ep = s.get("ep", 0)
            score_map[cid] = (ef, ep)

        # Build lookup by cid
        by_cid = {}
        for c in orig_constraints:
            cid = c.get("id") or c.get("cid")
            if cid:
                by_cid[cid] = c

        discriminative, over_approx, silent = [], [], []
        for cid, (ef, ep) in score_map.items():
            c = by_cid.get(cid, {"id": cid})
            if ef > 0 and ep == 0:
                discriminative.append(c)
            elif ep > 0:
                over_approx.append(c)
            else:
                silent.append(c)
        return discriminative, over_approx, silent

    def _do_one(json_file):
        func_name   = json_file.stem
        refined_out = os.path.join(refined_dir, f"{func_name}.json")
        merged_out  = os.path.join(merged_dir,  f"{func_name}.json")
        orig_c_path = os.path.join(c_dir, f"{func_name}.json")
        scores_path = os.path.join(scores_dir, f"{func_name}.json")

        if not os.path.exists(scores_path) or not os.path.exists(orig_c_path):
            return func_name, "skip (no scores/constraints)"
        if not force and os.path.exists(merged_out):
            return func_name, "skip (merged exists)"

        try:
            test_results = json.loads(json_file.read_text())
            scores_data  = json.loads(Path(scores_path).read_text())
            orig_data    = json.loads(Path(orig_c_path).read_text())

            orig_constraints = orig_data.get("constraints", [])
            constraint_scores = scores_data.get("constraint_scores", {})
            ranked_lines = scores_data.get("ranked_lines", [])

            disc, over, sil = _classify_constraints(constraint_scores, orig_constraints)

            # Build refinement prompt
            fn_name = test_results.get("target_function", func_name)
            ssa_code, def_map = _build_ssa_for(test_results.get("src_program", []), fn_name)

            prompt = build_refinement_prompt(
                program_code  = test_results.get("src_program", [""])[0],
                passing       = test_results.get("passing_tests", []),
                failing       = test_results.get("failing_tests", []),
                discriminative= disc,
                over_approx   = over,
                silent        = sil,
                ranked_lines  = ranked_lines,
                ssa_code      = ssa_code,
                def_map       = def_map,
            )

            # Query LLM directly with our already-built prompt
            from constraint_inference import (_query_gemini, _query_claude_vertex,
                                               _query_openai, _strip_json_fences)
            if model.startswith("gemini"):
                raw = _query_gemini(prompt, model, temperature=temperature)
            elif model.startswith("claude"):
                raw = _query_claude_vertex(prompt, model, temperature=temperature)
            else:
                raw = _query_openai(prompt, model, temperature=temperature)

            refined_constraints = json.loads(_strip_json_fences(raw))

            # Normalize to cbfl-ir-0.1 schema (LLMs sometimes produce flat schema)
            _normalize_constraints_to_cbfl_ir(refined_constraints)

            # Save refined-only constraints
            Path(refined_out).write_text(json.dumps(refined_constraints, indent=2))

            # Merge: combine original + refined constraints, renumber IDs
            merged = dict(orig_data)
            new_cs = refined_constraints.get("constraints", [])
            existing_ids = {c.get("id") for c in orig_constraints}
            # Prefix refined IDs with "R" to avoid collision
            for i, c in enumerate(new_cs, start=1):
                old_id = c.get("id", f"R{i}")
                new_id = f"R{i}" if old_id in existing_ids else old_id
                c["id"] = new_id
            merged["constraints"] = orig_constraints + new_cs
            Path(merged_out).write_text(json.dumps(merged, indent=2))

            return func_name, f"ok (+{len(new_cs)} refined constraints)"
        except Exception as e:
            return func_name, f"error: {e}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for func_name, status in pool.map(_do_one, exec_files):
            print(f"  [step3b] {func_name}: {status}")


def step4_instrument(working_dir: str, force: bool = False) -> None:
    """Instrument programs with LLM-generated constraints."""
    programs_dir = os.path.join(working_dir, "programs")
    constraints_dir = os.path.join(working_dir, "constraints")
    inst_dir = os.path.join(working_dir, "instrumented")
    os.makedirs(inst_dir, exist_ok=True)

    instrumenter = Instrumenter()
    for c_file in sorted(Path(constraints_dir).glob("*.json")):
        func_name = c_file.stem
        src_path = os.path.join(programs_dir, f"{func_name}.py")
        out_path = os.path.join(inst_dir, f"{func_name}.py")

        if not os.path.exists(src_path):
            print(f"[step4] No source for {func_name}, skipping")
            continue
        if not force and os.path.exists(out_path):
            print(f"[step4] Skip {func_name} (already instrumented)")
            continue

        with open(src_path) as f:
            src = f.read()
        with open(c_file) as f:
            constraint_str = f.read()

        try:
            instrumented = instrumenter.instrument(src, constraint_str)
            with open(out_path, "w") as f:
                f.write(instrumented)
            print(f"[step4] Instrumented {func_name}")
        except Exception as e:
            print(f"[step4] ERROR instrumenting {func_name}: {e}")


def step5_run_instrumented(working_dir: str, force: bool = False) -> None:
    """Run instrumented tests via pytest --inst; collect violations JSONL."""
    inst_dir = os.path.join(working_dir, "instrumented")
    violations_dir = os.path.join(working_dir, "violations")
    test_dir = os.path.join(working_dir, "testcases")
    os.makedirs(violations_dir, exist_ok=True)

    repo_root = os.path.dirname(os.path.abspath(__file__))

    for inst_file in sorted(Path(inst_dir).glob("*.py")):
        func_name = inst_file.stem
        violations_path = os.path.join(violations_dir, f"{func_name}.jsonl")
        if not force and os.path.exists(violations_path):
            print(f"[step5] Skip {func_name} (violations exist)")
            continue

        test_file = os.path.join(test_dir, f"test_{func_name}.py")
        if not os.path.exists(test_file):
            print(f"[step5] No test file for {func_name}, skipping")
            continue

        # Always remove the old violations file before running pytest.
        # conftest.py appends records on every run, so without this, repeated
        # executions accumulate duplicates that corrupt the violation matrix.
        if os.path.exists(violations_path):
            os.remove(violations_path)

        env = os.environ.copy()
        # Instrumented dir first so patched modules are imported.
        # repo_root (src/) must also be on PYTHONPATH so pytest can load
        # conftest.py (which registers --inst / --cbfl-report) as a plugin.
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(inst_dir) + ":" + repo_root + (":" + existing if existing else "")

        cmd = [
            sys.executable, "-m", "pytest",
            "-p", "conftest",   # explicitly load src/conftest.py plugin
            "--inst",
            f"--cbfl-report={violations_path}",
            "-v", "--tb=short",
            test_file,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env,
                                cwd=repo_root)
        ok = result.returncode in (0, 1)
        print(f"[step5] {func_name}: {'OK' if ok else 'ERROR'}")
        if not ok:
            print(result.stdout[-800:])
            print(result.stderr[-400:])


def step4b_instrument_merged(working_dir: str, force: bool = False) -> None:
    """Instrument programs with merged (original + refined) constraints."""
    programs_dir  = os.path.join(working_dir, "programs")
    merged_c_dir  = os.path.join(working_dir, "constraints_merged")
    inst_dir      = os.path.join(working_dir, "instrumented_merged")
    os.makedirs(inst_dir, exist_ok=True)

    instrumenter = Instrumenter()
    for c_file in sorted(Path(merged_c_dir).glob("*.json")):
        func_name = c_file.stem
        src_path  = os.path.join(programs_dir, f"{func_name}.py")
        out_path  = os.path.join(inst_dir,     f"{func_name}.py")
        if not os.path.exists(src_path):
            continue
        if not force and os.path.exists(out_path):
            continue
        try:
            src = Path(src_path).read_text()
            instrumented = instrumenter.instrument(src, c_file.read_text())
            Path(out_path).write_text(instrumented)
            print(f"[step4b] Instrumented {func_name}")
        except Exception as e:
            print(f"[step4b] ERROR {func_name}: {e}")


def step5b_run_merged(working_dir: str, force: bool = False) -> None:
    """Run merged-instrumented tests; collect violations into violations_merged/."""
    inst_dir    = os.path.join(working_dir, "instrumented_merged")
    viols_dir   = os.path.join(working_dir, "violations_merged")
    test_dir    = os.path.join(working_dir, "testcases")
    repo_root   = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(viols_dir, exist_ok=True)

    for inst_file in sorted(Path(inst_dir).glob("*.py")):
        func_name = inst_file.stem
        viol_path = os.path.join(viols_dir, f"{func_name}.jsonl")
        test_file = os.path.join(test_dir,  f"test_{func_name}.py")
        if not os.path.exists(test_file):
            continue
        if not force and os.path.exists(viol_path):
            continue
        if os.path.exists(viol_path):
            os.remove(viol_path)
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(inst_dir) + ":" + repo_root + (":" + existing if existing else "")
        cmd = [sys.executable, "-m", "pytest", "-p", "conftest", "--inst",
               f"--cbfl-report={viol_path}", "-v", "--tb=short", test_file]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                env=env, cwd=repo_root)
        ok = result.returncode in (0, 1)
        print(f"[step5b] {func_name}: {'OK' if ok else 'ERROR'}")


def step6b_compute_merged_spectrum(working_dir: str) -> Dict[str, Dict]:
    """Compute spectrum on merged violations + merged constraints; save to scores_merged/."""
    viols_dir   = os.path.join(working_dir, "violations_merged")
    merged_c    = os.path.join(working_dir, "constraints_merged")
    programs_dir= os.path.join(working_dir, "programs")
    scores_dir  = os.path.join(working_dir, "scores_merged")
    os.makedirs(scores_dir, exist_ok=True)

    all_results: Dict[str, Dict] = {}

    for v_file in sorted(Path(viols_dir).glob("*.jsonl")):
        func_name = v_file.stem
        c_file    = os.path.join(merged_c, f"{func_name}.json")
        src_file  = os.path.join(programs_dir, f"{func_name}.py")
        if not os.path.exists(c_file):
            continue

        raw_records = load_violations(str(v_file))
        records     = deduplicate_records(raw_records)
        with open(c_file) as f:
            _, constraints = parse_constraints(f.read())

        cids    = [c.cid for c in constraints]
        fn_name = constraints[0].fn_name if constraints else func_name
        vm      = build_matrix(records, cids, sut=fn_name)
        scores  = score_constraints(vm)
        ranked_c = rank_constraints(scores)

        src = Path(src_file).read_text() if os.path.exists(src_file) else ""
        line_scores = attribute_to_statements(scores, constraints, src) if src else {}
        ranked_lines = list(rank_lines(line_scores))

        result = {
            "n_passing":          len(vm.passing),
            "n_failing":          len(vm.failing),
            "constraint_scores":  scores,
            "ranked_constraints": ranked_c,
            "line_scores":        {str(k): v for k, v in line_scores.items()},
            "ranked_lines":       ranked_lines,
        }
        out_path = os.path.join(scores_dir, f"{func_name}.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        all_results[func_name] = result

    print(f"[step6b] Scored {len(all_results)} programs (merged constraints)")
    return all_results


def step6_compute_spectrum(
    working_dir: str,
    formula: str = "ochiai",
    scores_subdir: str = "scores",
    violations_subdir: str = "violations",
    constraints_subdir: str = "constraints",
) -> Dict[str, Dict]:
    """Build violation matrices; compute and save suspiciousness scores and line rankings."""
    violations_dir = os.path.join(working_dir, violations_subdir)
    constraints_dir = os.path.join(working_dir, constraints_subdir)
    programs_dir = os.path.join(working_dir, "programs")
    scores_dir = os.path.join(working_dir, scores_subdir)
    os.makedirs(scores_dir, exist_ok=True)

    all_results: Dict[str, Dict] = {}

    for v_file in sorted(Path(violations_dir).glob("*.jsonl")):
        func_name = v_file.stem
        c_file = os.path.join(constraints_dir, f"{func_name}.json")
        src_file = os.path.join(programs_dir, f"{func_name}.py")

        if not os.path.exists(c_file):
            print(f"[step6] No constraints for {func_name}, skipping")
            continue

        raw_records = load_violations(str(v_file))
        records = deduplicate_records(raw_records)
        n_dup = len(raw_records) - len(records)
        if n_dup:
            print(f"[step6] WARNING: {func_name}: removed {n_dup} duplicate record(s) from violations file")
        with open(c_file) as f:
            _, constraints = parse_constraints(f.read())

        cids = [c.cid for c in constraints]
        fn_name = constraints[0].fn_name if constraints else func_name
        vm = build_matrix(records, cids, sut=fn_name)
        scores = score_constraints(vm)
        ranked = rank_constraints(scores, formula=formula)

        src = ""
        line_scores: Dict[int, float] = {}
        if os.path.exists(src_file):
            with open(src_file) as f:
                src = f.read()
            line_scores = attribute_to_statements(scores, constraints, src, formula=formula)

        # Apply fault_line prior: LLM's predicted fault line is more reliable
        # than spectrum ranking alone; boost it so it ranks #1 unless a
        # strongly-firing constraint at another line clearly overrides it.
        from spectrum import apply_fault_line_prior
        c_json_data = {}
        with open(c_file) as f:
            c_json_data = json.load(f)
        fault_line_pred = c_json_data.get("fault_line")
        line_scores = apply_fault_line_prior(line_scores, fault_line_pred)

        result = {
            "n_passing": len(vm.passing),
            "n_failing": len(vm.failing),
            "constraint_scores": scores,
            "ranked_constraints": ranked,
            "line_scores": {str(k): v for k, v in line_scores.items()},
            "ranked_lines": [(ln, sc) for ln, sc in rank_lines(line_scores)],
            "fault_line_pred": fault_line_pred,
        }
        all_results[func_name] = result

        scores_path = os.path.join(scores_dir, f"{func_name}.json")
        with open(scores_path, "w") as f:
            json.dump(result, f, indent=2)

        print(
            f"[step6] {func_name}: "
            f"{len(vm.passing)}✓ {len(vm.failing)}✗  "
            f"top constraints={ranked[:3]}  "
            f"top lines={rank_lines(line_scores)[:3]}"
        )

    return all_results


def step7_counterfactual(working_dir: str, all_scores: Dict, model: str = "gemini-2.5-pro",
                         constraints_subdir: str = "constraints",
                         violations_subdir: str = "violations",
                         output_subdir: str = "refined",
                         workers: int = 1) -> None:
    """Run counterfactual verification for each program's top-ranked constraints."""
    import concurrent.futures as _cf_futures
    import threading as _threading
    from counterfactual import CounterfactualVerifier

    programs_dir = os.path.join(working_dir, "programs")
    constraints_dir = os.path.join(working_dir, constraints_subdir)
    test_dir = os.path.join(working_dir, "testcases")
    refined_dir = os.path.join(working_dir, output_subdir)
    os.makedirs(refined_dir, exist_ok=True)

    verifier = CounterfactualVerifier(model=model)

    # Canonical eval paths for counterfactual (test imports use dirname×3 == repo_root)
    eval_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation")
    canonical_programs = os.path.join(eval_dir, "programs")
    canonical_testcases = os.path.join(eval_dir, "testcases")

    def _process_one(item):
        func_name, result = item
        refined_path = os.path.join(refined_dir, f"{func_name}.json")
        if os.path.exists(refined_path):
            print(f"[step7] SKIP {func_name}: already done")
            return

        src_path = os.path.join(programs_dir, f"{func_name}.py")
        c_path = os.path.join(constraints_dir, f"{func_name}.json")
        # Use canonical testcases path so test's dirname×3 points to repo_root
        test_path_cf = os.path.join(canonical_testcases, f"test_{func_name}.py")
        test_path_wd = os.path.join(test_dir, f"test_{func_name}.py")
        test_path = test_path_cf if os.path.exists(test_path_cf) else test_path_wd
        # Use canonical src_path for correct import resolution inside tmpdir
        canonical_src = os.path.join(canonical_programs, f"{func_name}.py")
        cf_src_path = canonical_src if os.path.exists(canonical_src) else src_path

        if not all(os.path.exists(p) for p in [src_path, c_path, test_path]):
            print(f"[step7] Missing files for {func_name}, skipping")
            return

        with open(src_path) as f:
            fn_src = f.read()
        with open(c_path) as f:
            _, constraints = parse_constraints(f.read())

        c_by_id = {c.cid: c for c in constraints}

        # Build ranked list: (constraint, ochiai_score, first_anchor_line)
        ranked: List[Tuple] = []
        for cid, score in result["ranked_constraints"]:
            c = c_by_id.get(cid)
            if c is None:
                continue
            lines = find_anchor_lines(c, fn_src)
            anchor_line = lines[0] if lines else 1
            ranked.append((c, score, anchor_line))

        violations_path = os.path.join(working_dir, violations_subdir, f"{func_name}.jsonl")

        print(f"[step7] Counterfactual for {func_name} (top 5 constraints)…")
        try:
            cf_results = verifier.run(
                ranked[:5], fn_src, cf_src_path, test_path,
                violations_path=violations_path if os.path.exists(violations_path) else None,
            )
        except Exception as e:
            print(f"[step7] ERROR {func_name}: {e}")
            return

        out = [
            {
                "cid": r.constraint.cid,
                "status": r.status,
                "patch": r.patch,
                "original_failing": r.original_failing,
                "patched_failing": r.patched_failing,
                "pruned": r.pruned,
                "prune_reason": r.prune_reason,
            }
            for r in cf_results
        ]

        with open(refined_path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"[step7] {func_name}: {[(r['cid'], r['status']) for r in out]}")

    items = list(all_scores.items())
    if workers > 1:
        with _cf_futures.ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(_process_one, items))
    else:
        for item in items:
            _process_one(item)


def _count_executable_lines(src: str) -> int:
    """Count non-blank, non-comment lines as a proxy for inspectable statements."""
    count = 0
    for line in src.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            count += 1
    return count


def step8_report_metrics(
    working_dir: str,
    all_scores: Dict,
    run_baselines: bool = False,
    scores_subdir: str = "scores",
    results_subdir: str = "results",
    refined_subdir: str = "refined",
) -> None:
    """Compute and save RQ1/RQ2/RQ3 metrics to results/ directory."""
    programs_dir = os.path.join(working_dir, "programs")
    refined_dir = os.path.join(working_dir, refined_subdir)
    results_dir = os.path.join(working_dir, results_subdir)
    os.makedirs(results_dir, exist_ok=True)

    # Load ground truth for top-k accuracy
    gt_path = os.path.join(working_dir, "ground_truth.json")
    gt_by_file: Dict[str, List[int]] = {}
    if os.path.exists(gt_path):
        with open(gt_path) as f:
            gt = json.load(f)
        for entry in gt.get("programs", []):
            fname = entry["file"].replace(".py", "")
            gt_by_file[fname] = entry.get("faulty_lines", [])

    # Optional baseline computation
    baselines_cache: Dict[str, Dict] = {}
    if run_baselines:
        from baselines import sbfl_run, dd_run
        repo_root = os.path.dirname(os.path.abspath(__file__))
        test_dir = os.path.join(working_dir, "testcases")
        baselines_dir = os.path.join(working_dir, "results", "baselines")
        os.makedirs(baselines_dir, exist_ok=True)

        for func_name in sorted(all_scores.keys()):
            src_path = os.path.join(programs_dir, f"{func_name}.py")
            test_path = os.path.join(test_dir, f"test_{func_name}.py")
            if not all(os.path.exists(p) for p in [src_path, test_path]):
                continue

            cached_path = os.path.join(baselines_dir, f"{func_name}.json")
            if os.path.exists(cached_path):
                with open(cached_path) as f:
                    baselines_cache[func_name] = json.load(f)
                print(f"[step8/baselines] {func_name}: loaded cached baselines")
                continue

            print(f"[step8/baselines] {func_name}: running SBFL…")
            sbfl_result = sbfl_run(src_path, test_path, repo_root)
            print(f"[step8/baselines] {func_name}: SBFL {sbfl_result['pct_suspicious']}%  running DD…")
            dd_result = dd_run(src_path, test_path, repo_root, max_iterations=80)
            print(f"[step8/baselines] {func_name}: DD {dd_result['pct_suspicious']}% ({dd_result['dd_iterations']} iters)")

            entry = {"sbfl": sbfl_result, "dd": dd_result}
            with open(cached_path, "w") as f:
                json.dump(entry, f, indent=2)
            baselines_cache[func_name] = entry

    rq1_rows = []
    rq2_rows = []
    rq3_rows = []

    for func_name, result in all_scores.items():
        ranked_lines = result.get("ranked_lines", [])
        ranked_constraints = result.get("ranked_constraints", [])
        constraint_scores = result.get("constraint_scores", {})

        src_path = os.path.join(programs_dir, f"{func_name}.py")
        src = ""
        n_lines_exec = 0
        if os.path.exists(src_path):
            with open(src_path) as f:
                src = f.read()
            n_lines_exec = _count_executable_lines(src)

        n_suspicious = len(ranked_lines)
        pct_suspicious = (100.0 * n_suspicious / n_lines_exec) if n_lines_exec else 0.0

        # Top-k accuracy (whether any faulty line appears in top-k)
        faulty_lines = gt_by_file.get(func_name, [])
        ranked_line_nums = [ln for ln, _ in ranked_lines]
        top_1 = any(ln in ranked_line_nums[:1] for ln in faulty_lines) if faulty_lines else None
        top_3 = any(ln in ranked_line_nums[:3] for ln in faulty_lines) if faulty_lines else None
        top_5 = any(ln in ranked_line_nums[:5] for ln in faulty_lines) if faulty_lines else None
        # Best rank of any faulty line
        best_rank = min(
            (ranked_line_nums.index(ln) + 1 for ln in faulty_lines if ln in ranked_line_nums),
            default=None,
        )

        # Baseline columns (filled only if run_baselines=True)
        bl = baselines_cache.get(func_name, {})
        sbfl_pct = bl.get("sbfl", {}).get("pct_suspicious", None)
        dd_pct   = bl.get("dd",   {}).get("pct_suspicious", None)

        # --- RQ1: localization precision ---
        row_rq1: Dict = {
            "function": func_name,
            "n_passing": result.get("n_passing", 0),
            "n_failing": result.get("n_failing", 0),
            "n_suspicious_lines": n_suspicious,
            "n_executable_lines": n_lines_exec,
            "pct_suspicious": round(pct_suspicious, 1),
            "top_1_line": ranked_line_nums[0] if ranked_line_nums else None,
            "faulty_lines": faulty_lines,
            "best_rank": best_rank,
            "top1_acc": int(top_1) if top_1 is not None else "N/A",
            "top3_acc": int(top_3) if top_3 is not None else "N/A",
            "top5_acc": int(top_5) if top_5 is not None else "N/A",
            "sbfl_pct_suspicious": sbfl_pct if sbfl_pct is not None else "N/A",
            "dd_pct_suspicious": dd_pct if dd_pct is not None else "N/A",
        }

        # --- RQ2: counterfactual ablation ---
        refined_path = os.path.join(refined_dir, f"{func_name}.json")
        primary_cid = None
        cf_pct_suspicious = pct_suspicious  # without CF: same as above

        if os.path.exists(refined_path):
            with open(refined_path) as f:
                refined = json.load(f)
            primaries = [r for r in refined if r["status"] == "Primary"]

            if primaries:
                primary_cid = primaries[0]["cid"]

            # After CF: keep only non-pruned Primary/Secondary constraints.
            # Re-compute line scores using only those constraint scores.
            # If CF found nothing useful, suspicious % stays at baseline (no pruning).
            kept_cids = {r["cid"] for r in refined
                         if r["status"] in ("Primary", "Secondary") and not r.get("pruned")}
            pruned_cids = {r["cid"] for r in refined
                           if r.get("pruned") or r["status"] in ("OverApproximate", "Irrelevant")}
            # Constraints not in refined were skipped after an early Primary break.
            # They are implicitly pruned when at least one Primary was found.
            if primaries:
                all_scored_cids = set(constraint_scores.keys())
                refined_cids = {r["cid"] for r in refined}
                pruned_cids |= all_scored_cids - refined_cids
            actually_pruned = pruned_cids & set(constraint_scores.keys())

            if kept_cids and actually_pruned:
                # At least one constraint was pruned and at least one was kept → re-compute
                cf_constraint_scores = {cid: s for cid, s in constraint_scores.items()
                                         if cid in kept_cids}
                c_path = os.path.join(working_dir, "constraints", f"{func_name}.json")
                if src and os.path.exists(c_path):
                    from instrumentation import parse_constraints as _pc
                    with open(c_path) as f:
                        _, _constraints = _pc(f.read())
                    cf_line_scores_map = attribute_to_statements(cf_constraint_scores, _constraints, src)
                    cf_n_suspicious = len(cf_line_scores_map)
                    cf_pct_suspicious = (100.0 * cf_n_suspicious / n_lines_exec) if n_lines_exec else 0.0
                # else: no src, keep baseline
            # If CF found nothing, leave cf_pct_suspicious at pct_suspicious (baseline)

        row_rq2: Dict = {
            "function": func_name,
            "pct_suspicious_before_cf": round(pct_suspicious, 1),
            "pct_suspicious_after_cf": round(cf_pct_suspicious, 1),
            "improvement_pp": round(pct_suspicious - cf_pct_suspicious, 1),
            "primary_constraint": primary_cid or "N/A",
            "cf_available": os.path.exists(refined_path),
        }

        # --- RQ3: constraint quality ---
        n_constraints = len(constraint_scores)
        n_violated = sum(1 for s in constraint_scores.values() if s.get("ef", 0) > 0)
        n_over_approx = sum(1 for s in constraint_scores.values() if s.get("ep", 0) > 0 and s.get("ef", 0) > 0)
        n_pruned = 0
        if os.path.exists(refined_path):
            with open(refined_path) as f:
                refined_data = json.load(f)
            n_pruned = sum(1 for r in refined_data if r.get("pruned") or r.get("status") == "OverApproximate")

        row_rq3: Dict = {
            "function": func_name,
            "n_constraints": n_constraints,
            "n_violated_on_failing": n_violated,
            "n_over_approximate": n_over_approx,
            "n_pruned_by_cf": n_pruned,
            "pct_violated": round(100.0 * n_violated / n_constraints, 1) if n_constraints else 0.0,
        }

        rq1_rows.append(row_rq1)
        rq2_rows.append(row_rq2)
        rq3_rows.append(row_rq3)

        print(
            f"  {func_name}: {pct_suspicious:.1f}% suspicious  "
            f"best_rank={best_rank}  top1={top_1}  "
            f"primary={primary_cid or 'N/A'}"
        )

    def _write_csv(path, rows):
        if not rows:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow({k: (json.dumps(v) if isinstance(v, list) else v) for k, v in row.items()})

    _write_csv(os.path.join(results_dir, "rq1_localization.csv"), rq1_rows)
    _write_csv(os.path.join(results_dir, "rq2_counterfactual.csv"), rq2_rows)
    _write_csv(os.path.join(results_dir, "rq3_constraints.csv"), rq3_rows)

    # Aggregate summary
    if rq1_rows:
        n_progs = len(rq1_rows)
        mean_pct = sum(r["pct_suspicious"] for r in rq1_rows) / n_progs
        top1_acc = [r["top1_acc"] for r in rq1_rows if r["top1_acc"] != "N/A"]
        top3_acc = [r["top3_acc"] for r in rq1_rows if r["top3_acc"] != "N/A"]
        top5_acc = [r["top5_acc"] for r in rq1_rows if r["top5_acc"] != "N/A"]
        all_ranks = sorted(r["best_rank"] for r in rq1_rows if isinstance(r.get("best_rank"), int))
        median_rank = all_ranks[len(all_ranks) // 2] if all_ranks else "N/A"
        mean_improve = sum(r["improvement_pp"] for r in rq2_rows) / len(rq2_rows) if rq2_rows else 0.0
        total_constraints = sum(r["n_constraints"] for r in rq3_rows)
        total_violated = sum(r["n_violated_on_failing"] for r in rq3_rows)

        sbfl_pcts = [r["sbfl_pct_suspicious"] for r in rq1_rows if isinstance(r["sbfl_pct_suspicious"], (int, float))]
        dd_pcts   = [r["dd_pct_suspicious"]   for r in rq1_rows if isinstance(r["dd_pct_suspicious"],   (int, float))]

        summary = {
            "n_programs": n_progs,
            "rq1": {
                "mean_pct_suspicious": round(mean_pct, 1),
                "top1_accuracy": round(sum(top1_acc) / len(top1_acc), 3) if top1_acc else "N/A",
                "top3_accuracy": round(sum(top3_acc) / len(top3_acc), 3) if top3_acc else "N/A",
                "top5_accuracy": round(sum(top5_acc) / len(top5_acc), 3) if top5_acc else "N/A",
                "median_rank": median_rank,
                "baselines": {
                    "sbfl_mean_pct_suspicious": round(sum(sbfl_pcts) / len(sbfl_pcts), 1) if sbfl_pcts else "N/A",
                    "dd_mean_pct_suspicious":   round(sum(dd_pcts)   / len(dd_pcts),   1) if dd_pcts   else "N/A",
                },
                "per_program": {r["function"]: {"pct_suspicious": r["pct_suspicious"], "best_rank": r["best_rank"]} for r in rq1_rows},
            },
            "rq2": {
                "mean_improvement_pp": round(mean_improve, 1),
                "per_program": {r["function"]: {"before": r["pct_suspicious_before_cf"], "after": r["pct_suspicious_after_cf"]} for r in rq2_rows},
            },
            "rq3": {
                "total_constraints": total_constraints,
                "total_violated": total_violated,
                "pct_violated": round(100.0 * total_violated / total_constraints, 1) if total_constraints else 0.0,
                "per_program": {r["function"]: r for r in rq3_rows},
            },
        }
        summary_path = os.path.join(results_dir, "summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n[step8] Summary: mean_suspicious={mean_pct:.1f}%  top1={summary['rq1']['top1_accuracy']}  mean_CF_improve={mean_improve:.1f}pp")
        print(f"[step8] Results saved to {results_dir}/")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="SemLoc end-to-end evaluation runner")
    parser.add_argument("--working-dir", default="./example_pipeline", metavar="DIR")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip steps 2–3 (use existing constraints)",
    )
    parser.add_argument(
        "--skip-counterfactual",
        action="store_true",
        help="Skip step 7 (counterfactual verification)",
    )
    parser.add_argument(
        "--cf-disabled",
        action="store_true",
        help="Disable counterfactual reasoning; use semantic indexing only (steps 3b→4b→5b→6b)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run all steps even if outputs already exist",
    )
    parser.add_argument(
        "--steps",
        default="1,2,3,4,5,6,7,8",
        help="Comma-separated list of steps to run (default: all)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-pro",
        help="LLM model for constraint inference (e.g. gpt-4o, gemini-2.0-flash)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="LLM temperature for constraint inference (default: 0.3)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Parallel workers for step 3 LLM queries (default: 8)",
    )
    parser.add_argument(
        "--baselines",
        action="store_true",
        help="Compute SBFL and DD baselines in step 8 (slow; cached per program)",
    )
    parser.add_argument(
        "--cf-on-refined",
        action="store_true",
        help="Run counterfactual verification (step 7) on merged scores (requires prior --cf-disabled run)",
    )
    parser.add_argument(
        "--cf-on-base",
        action="store_true",
        help="Run counterfactual verification (step 7) on base spectrum scores; saves to refined_base_cf/ and results_cf_base/",
    )
    parser.add_argument(
        "--spectrum-formula",
        choices=["ochiai", "tarantula"],
        default="ochiai",
        help="Suspiciousness formula for spectrum scoring (default: ochiai)",
    )
    parser.add_argument(
        "--disable-semantic-index",
        action="store_true",
        help="Run semantic indexing disabled baseline (direct LLM fault localization, no constraint infrastructure)",
    )
    args = parser.parse_args()

    # Route --disable-semantic-index to llm_direct_fl
    if args.disable_semantic_index:
        import llm_direct_fl
        llm_direct_fl.run_experiment(
            working_dir=args.working_dir,
            n_runs=1,
            model=args.model,
            force=args.force,
            dry_run=False,
            temperature=args.temperature,
            workers=args.workers,
        )
        return

    wd = args.working_dir
    steps = set(args.steps.split(","))
    force = args.force

    print(f"[run_eval] Working dir: {wd}")

    if "1" in steps:
        print("\n=== Step 1: Run tests ===")
        step1_run_tests(wd, force)

    if "2" in steps and not args.skip_llm:
        print("\n=== Step 2: Build prompts ===")
        step2_build_prompts(wd, force)

    if "3" in steps and not args.skip_llm:
        print("\n=== Step 3: Query LLM for constraints ===")
        step3_query_llm(wd, force, model=args.model, temperature=args.temperature, workers=args.workers)

    if "4" in steps:
        print("\n=== Step 4: Instrument programs ===")
        step4_instrument(wd, force)

    if "5" in steps:
        print("\n=== Step 5: Run instrumented tests ===")
        step5_run_instrumented(wd, force)

    # Step 6 must run before 7 and 8 (or we load from disk)
    all_scores: Dict[str, Dict] = {}
    if "6" in steps:
        print("\n=== Step 6: Compute spectrum ===")
        all_scores = step6_compute_spectrum(wd, formula=args.spectrum_formula)
    else:
        scores_dir = os.path.join(wd, "scores")
        if os.path.exists(scores_dir):
            for s_file in sorted(Path(scores_dir).glob("*.json")):
                with open(s_file) as f:
                    all_scores[s_file.stem] = json.load(f)

    if "7" in steps and not args.skip_counterfactual and all_scores:
        print("\n=== Step 7: Counterfactual verification ===")
        step7_counterfactual(wd, all_scores, model=args.model, workers=args.workers)

    merged_scores: Dict[str, Dict] = {}
    if args.cf_disabled and all_scores:
        print("\n=== Step 3b: Re-infer constraints (CF disabled) ===")
        step3b_iterative_refine(wd, force, model=args.model,
                                temperature=args.temperature, workers=args.workers)
        print("\n=== Step 4b: Instrument with merged constraints ===")
        step4b_instrument_merged(wd, force)
        print("\n=== Step 5b: Run merged instrumented tests ===")
        step5b_run_merged(wd, force)
        print("\n=== Step 6b: Compute merged spectrum ===")
        merged_scores = step6b_compute_merged_spectrum(wd)
        if merged_scores:
            print("\n=== Step 8 (CF disabled): Report metrics ===")
            step8_report_metrics(wd, merged_scores, run_baselines=False,
                                 scores_subdir="scores_merged",
                                 results_subdir="results_refined")
    elif not merged_scores:
        # Load existing merged scores from disk if refinement was already run
        scores_merged_dir = os.path.join(wd, "scores_merged")
        if os.path.exists(scores_merged_dir):
            for s_file in sorted(Path(scores_merged_dir).glob("*.json")):
                with open(s_file) as f:
                    merged_scores[s_file.stem] = json.load(f)

    # CF on merged scores (if --cf-on-refined and refinement produced scores)
    if getattr(args, "cf_on_refined", False) and merged_scores and not args.skip_counterfactual:
        print("\n=== Step 7 (CF on merged): Counterfactual verification on merged scores ===")
        step7_counterfactual(wd, merged_scores, model=args.model,
                             constraints_subdir="constraints_merged",
                             violations_subdir="violations_merged",
                             output_subdir="refined_cf",
                             workers=args.workers)
        # Re-report metrics after CF
        print("\n=== Step 8 (CF on merged): Report metrics ===")
        step8_report_metrics(wd, merged_scores, run_baselines=False,
                             scores_subdir="scores_merged",
                             results_subdir="results_cf_refined",
                             refined_subdir="refined_cf")

    # CF on base scores (if --cf-on-base)
    if getattr(args, "cf_on_base", False) and all_scores and not args.skip_counterfactual:
        print("\n=== Step 7 (CF on base): Counterfactual verification on base spectrum scores ===")
        step7_counterfactual(wd, all_scores, model=args.model,
                             constraints_subdir="constraints",
                             violations_subdir="violations",
                             output_subdir="refined_base_cf",
                             workers=args.workers)
        print("\n=== Step 8 (CF-base): Report metrics ===")
        step8_report_metrics(wd, all_scores, run_baselines=False,
                             scores_subdir="scores",
                             results_subdir="results_cf_base",
                             refined_subdir="refined_base_cf")

    if "8" in steps and all_scores:
        print("\n=== Step 8: Report metrics ===")
        step8_report_metrics(wd, all_scores, run_baselines=args.baselines)

    print("\n[run_eval] Done.")


if __name__ == "__main__":
    main()
