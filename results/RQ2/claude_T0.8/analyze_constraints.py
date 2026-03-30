#!/usr/bin/env python3
"""
analyze_constraints.py — Self-contained constraint quality analysis for SemLoc RQ2.

Reads constraints/, violations/, scores/, and ground_truth.json from the same
directory, then prints the constraint quality statistics used in the paper
(Table: constraint_analysis, and Table: rq2_ablation).

Usage:
    cd results/RQ2/claude_T0.8
    python analyze_constraints.py

    # Or specify a different working directory:
    python analyze_constraints.py --dir /path/to/results/RQ2/claude_T0.8
"""

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_constraints(constraints_dir: str) -> Dict[str, dict]:
    """Load all constraint JSON files. Returns {func_name: constraints_obj}."""
    result = {}
    for path in sorted(Path(constraints_dir).glob("*.json")):
        with open(path) as f:
            result[path.stem] = json.load(f)
    return result


def load_violations(violations_dir: str) -> Dict[str, List[dict]]:
    """Load all violation JSONL files. Returns {func_name: [record, ...]}."""
    result = {}
    for path in sorted(Path(violations_dir).glob("*.jsonl")):
        records = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        result[path.stem] = records
    return result


def load_scores(scores_dir: str) -> Dict[str, dict]:
    """Load all score JSON files. Returns {func_name: scores_obj}."""
    result = {}
    for path in sorted(Path(scores_dir).glob("*.json")):
        with open(path) as f:
            result[path.stem] = json.load(f)
    return result


def load_ground_truth(gt_path: str) -> Dict[str, List[int]]:
    """Load ground_truth.json. Returns {func_name: [faulty_line, ...]}."""
    with open(gt_path) as f:
        data = json.load(f)
    result = {}
    for entry in data.get("programs", []):
        name = entry["file"].replace(".py", "")
        result[name] = entry.get("faulty_lines", [])
    return result


# ---------------------------------------------------------------------------
# Constraint classification
# ---------------------------------------------------------------------------

def classify_constraints(
    func_name: str,
    constraints_obj: dict,
    violation_records: List[dict],
) -> Dict[str, dict]:
    """
    Classify each constraint by its runtime behavior:
      - Discriminative: violated only on failing tests (ef > 0, ep == 0)
      - Over-approximate: violated on both failing and passing tests (ef > 0, ep > 0)
      - Irrelevant: never violated (ef == 0)

    Returns {cid: {"ef": int, "ep": int, "category": str, "region": str}}
    """
    constraints = constraints_obj.get("constraints", [])
    fn_name = constraints_obj.get("function_name", func_name)

    # Build per-constraint ef/ep counts from violation records
    ef_per_cid: Dict[str, int] = defaultdict(int)
    ep_per_cid: Dict[str, int] = defaultdict(int)

    for record in violation_records:
        outcome = record.get("outcome", "")
        for violation in record.get("violations", []):
            # violation is (sut_id, cid, reason) or [sut_id, cid, reason]
            if isinstance(violation, (list, tuple)) and len(violation) >= 2:
                cid = str(violation[1])
            elif isinstance(violation, dict):
                cid = str(violation.get("cid", ""))
            else:
                continue
            if outcome == "passed":
                ep_per_cid[cid] += 1
            else:
                ef_per_cid[cid] += 1

    result = {}
    for c in constraints:
        cid = str(c.get("cid", c.get("id", "")))
        ef = ef_per_cid.get(cid, 0)
        ep = ep_per_cid.get(cid, 0)
        if ef > 0 and ep == 0:
            cat = "discriminative"
        elif ef > 0 and ep > 0:
            cat = "over_approximate"
        else:
            cat = "irrelevant"
        region = c.get("region") or c.get("instrument", {}).get("region", "UNKNOWN")
        result[cid] = {
            "ef": ef,
            "ep": ep,
            "category": cat,
            "region": region,
        }

    return result


def get_best_rank(func_name: str, scores_obj: dict, gt_lines: List[int]) -> Optional[int]:
    """
    Given a scores object (which includes ranked lines), return the best rank
    (1-indexed) of any faulty line, or None if no faulty line appears in ranked list.
    """
    # scores_obj may have different structures; try common formats
    ranked = scores_obj.get("ranked_lines", [])
    if not ranked:
        # Try alternative key
        ranked = scores_obj.get("lines", [])

    if not ranked:
        return None

    # ranked is a list of (line_no, score) or {"line": ..., "score": ...}
    ranked_lines = []
    for item in ranked:
        if isinstance(item, (list, tuple)):
            ranked_lines.append(int(item[0]))
        elif isinstance(item, dict):
            ranked_lines.append(int(item.get("line", 0)))

    best = None
    for fl in gt_lines:
        try:
            rank = ranked_lines.index(fl) + 1
            best = rank if best is None else min(best, rank)
        except ValueError:
            pass
    return best


# ---------------------------------------------------------------------------
# Region constants
# ---------------------------------------------------------------------------

REGIONS = ["LINE", "AFTER_DEF", "AFTER_BRANCH", "BEFORE_USE", "LOOP_TAIL", "ANY_RETURN"]


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_analysis(base_dir: str) -> None:
    constraints_dir = os.path.join(base_dir, "constraints")
    violations_dir  = os.path.join(base_dir, "violations")
    scores_dir      = os.path.join(base_dir, "scores")
    gt_path         = os.path.join(base_dir, "ground_truth.json")
    cf_summary_path = os.path.join(base_dir, "results_cf_base", "summary.json")

    print("Loading data...")
    all_constraints = load_constraints(constraints_dir)
    all_violations  = load_violations(violations_dir)
    all_scores      = load_scores(scores_dir)
    gt              = load_ground_truth(gt_path)

    programs = sorted(set(all_constraints) & set(all_violations) & set(all_scores) & set(gt))
    N = len(programs)
    print(f"Programs: {N}")

    # Load CF-scored results for Primary/Secondary classification
    cf_summary = {}
    if os.path.exists(cf_summary_path):
        with open(cf_summary_path) as f:
            cf_summary = json.load(f)
    per_prog_cf = cf_summary.get("rq1", {}).get("per_program", {})

    def is_acc3(func_name: str) -> bool:
        """True if SemLoc localizes this program within top-3."""
        info = per_prog_cf.get(func_name, {})
        rank = info.get("best_rank")
        return rank is not None and rank <= 3

    # -----------------------------------------------------------------------
    # Constraint classification per program
    # -----------------------------------------------------------------------

    # Program-level counters
    prog_any_violated  = 0  # ≥1 ef > 0 (any)
    prog_discriminative = 0  # ≥1 ef > 0, ep == 0
    prog_only_approx    = 0  # any violated but none discriminative
    prog_none_violated  = 0  # all ef == 0

    # Constraint-level counters
    total_constraints   = 0
    n_discriminative    = 0
    n_primary           = 0  # discriminative + program in Acc@3
    n_secondary         = 0  # discriminative but program not in Acc@3
    n_over_approx       = 0
    n_irrelevant        = 0

    # Region-level counters
    region_coverage    = defaultdict(int)  # programs with ≥1 violated in this region
    region_total       = defaultdict(int)  # total constraints per region
    region_discrim     = defaultdict(int)  # discriminative constraints per region

    for func_name in programs:
        cobj  = all_constraints[func_name]
        vrecs = all_violations.get(func_name, [])
        class_info = classify_constraints(func_name, cobj, vrecs)

        total_constraints += len(class_info)
        has_any_violated   = False
        has_discriminative = False

        for cid, info in class_info.items():
            cat    = info["category"]
            region = info["region"]

            region_total[region] += 1

            if cat == "discriminative":
                n_discriminative += 1
                region_discrim[region] += 1
                has_any_violated    = True
                has_discriminative  = True
                if is_acc3(func_name):
                    n_primary += 1
                else:
                    n_secondary += 1
            elif cat == "over_approximate":
                n_over_approx += 1
                has_any_violated = True
            else:
                n_irrelevant += 1

        # Region coverage: any violated (ef > 0) in this region?
        for cid, info in class_info.items():
            if info["ef"] > 0:
                region_coverage[info["region"]] += 1
                # Only count once per program per region
                break  # BUG: this breaks after first region — fix below

        # Fix: count per region properly
        # (reset and recount)

        # Count per program
        if has_any_violated:
            prog_any_violated += 1
            if has_discriminative:
                prog_discriminative += 1
            else:
                prog_only_approx += 1
        else:
            prog_none_violated += 1

    # Recount region_coverage properly (per program, per region)
    region_coverage = defaultdict(int)
    region_discrim_prog = defaultdict(int)  # programs with ≥1 discriminative in region

    for func_name in programs:
        cobj  = all_constraints[func_name]
        vrecs = all_violations.get(func_name, [])
        class_info = classify_constraints(func_name, cobj, vrecs)

        regions_with_violated = set()
        regions_with_discrim  = set()
        for cid, info in class_info.items():
            r = info["region"]
            if info["ef"] > 0:
                regions_with_violated.add(r)
            if info["category"] == "discriminative":
                regions_with_discrim.add(r)

        for r in regions_with_violated:
            region_coverage[r] += 1
        for r in regions_with_discrim:
            region_discrim_prog[r] += 1

    # -----------------------------------------------------------------------
    # Print results
    # -----------------------------------------------------------------------

    n_violated = n_discriminative + n_over_approx

    print()
    print("=" * 65)
    print("CONSTRAINT QUALITY ANALYSIS (Table: constraint_analysis)")
    print("=" * 65)
    print(f"\n--- Semantic index: program-level coverage ({N} programs) ---")
    print(f"Total constraints inferred:          {total_constraints:>6}")
    print(f"Mean constraints per program:        {total_constraints/N:>6.2f}")
    print(f"Programs with ≥1 violated:           {prog_any_violated:>6}  ({100*prog_any_violated/N:.1f}%)")
    print(f"  w/ ≥1 discriminative:              {prog_discriminative:>6}  ({100*prog_discriminative/N:.1f}%)")
    print(f"  w/ only over-approximate:          {prog_only_approx:>6}  ({100*prog_only_approx/N:.1f}%)")
    print(f"Programs with zero violated:         {prog_none_violated:>6}  ({100*prog_none_violated/N:.1f}%)")

    print(f"\n--- Constraint quality profile (of {total_constraints} constraints) ---")
    print(f"Discriminative (clean signal):       {n_discriminative:>6}  ({100*n_discriminative/total_constraints:.1f}%)")
    print(f"  Primary (contributes to Acc@3):    {n_primary:>6}  ({100*n_primary/total_constraints:.1f}%)")
    print(f"  Secondary (signal, Acc@3 miss):    {n_secondary:>6}  ({100*n_secondary/total_constraints:.1f}%)")
    print(f"Over-approximate (noisy):            {n_over_approx:>6}  ({100*n_over_approx/total_constraints:.1f}%)")
    print(f"Irrelevant (never triggered):        {n_irrelevant:>6}  ({100*n_irrelevant/total_constraints:.1f}%)")

    print(f"\n--- Of {n_violated} violated constraints ({100*n_violated/total_constraints:.1f}% of total) ---")
    if n_violated > 0:
        print(f"Discriminative:                      {n_discriminative:>6}  ({100*n_discriminative/n_violated:.1f}%)")
        print(f"Over-approximate:                    {n_over_approx:>6}  ({100*n_over_approx/n_violated:.1f}%)")
    else:
        print(f"Discriminative:                      {n_discriminative:>6}  (N/A — 0 violated)")
        print(f"Over-approximate:                    {n_over_approx:>6}  (N/A — 0 violated)")

    print()
    print("=" * 65)
    print("REGION COVERAGE (Table: rq2_ablation — coverage column)")
    print("=" * 65)
    print(f"{'Region':<20} {'#C':>5} {'Coverage':>12} {'Discrim%':>10} {'DiscrimProgs':>14}")
    print("-" * 65)
    for region in REGIONS:
        total_r   = region_total.get(region, 0)
        coverage  = region_coverage.get(region, 0)
        discrim_r = region_discrim.get(region, 0)
        discrim_p = region_discrim_prog.get(region, 0)
        pct = 100 * discrim_r / total_r if total_r > 0 else 0
        print(f"{region:<20} {total_r:>5} {coverage:>5}/{N:<5}  {pct:>8.0f}%  {discrim_p:>5}/{N}")

    # Show any regions not in REGIONS list (e.g. ENTRY, LOOP_HEAD)
    extra_regions = [r for r in region_total if r not in REGIONS]
    for region in sorted(extra_regions):
        total_r   = region_total.get(region, 0)
        coverage  = region_coverage.get(region, 0)
        discrim_r = region_discrim.get(region, 0)
        discrim_p = region_discrim_prog.get(region, 0)
        pct = 100 * discrim_r / total_r if total_r > 0 else 0
        print(f"{region:<20} {total_r:>5} {coverage:>5}/{N:<5}  {pct:>8.0f}%  {discrim_p:>5}/{N}")

    print()
    print("Note: 'Primary' = discriminative constraint where faulty line is in top-3 (Acc@3).")
    print("      'Secondary' = discriminative but program not localized at Acc@3.")
    if not per_prog_cf:
        print("WARNING: results_cf_base/summary.json not found.")
        print("         Primary/Secondary classification is UNAVAILABLE.")
        print("         Re-run step 8 (CF scoring) to generate it:")
        print("         python ../../src/run_eval.py --working-dir . --steps 8 --cf-on-base")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Constraint quality analysis for SemLoc RQ2"
    )
    parser.add_argument(
        "--dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to the working directory containing constraints/, violations/, scores/",
    )
    args = parser.parse_args()
    run_analysis(args.dir)
