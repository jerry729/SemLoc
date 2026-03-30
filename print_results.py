#!/usr/bin/env python3
"""
print_results.py — Print Table 1 (RQ1) from pre-computed results.

Reads all result directories under results/RQ1/ and prints:
  Acc@1, Acc@3, Acc@5, Med.Rank, %Susp

Usage (from artifact root):
    python print_results.py          # Table 1 (RQ1: all configurations)
    python print_results.py --rq2    # RQ2: constraint quality summary
    python print_results.py --rq3    # RQ3: BugsInPy summary
"""

import argparse
import csv
import json
import os
import glob
import statistics
from pathlib import Path
from typing import Optional


ARTIFACT_ROOT = os.path.dirname(os.path.abspath(__file__))
RQ1_DIR  = os.path.join(ARTIFACT_ROOT, "results", "RQ1")
RQ2_DIR  = os.path.join(ARTIFACT_ROOT, "results", "RQ2", "claude_T0.8")
RQ3_DIR  = os.path.join(ARTIFACT_ROOT, "results", "RQ3", "bugsInPy_results")
GT_PATH  = os.path.join(ARTIFACT_ROOT, "benchmark", "ground_truth.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(v):
    if v is None or v == "N/A":
        return "N/A"
    return f"{v*100:.1f}%"

def _fmt(v, decimals=1):
    if v is None or v == "N/A":
        return "N/A"
    return f"{v:.{decimals}f}"


def load_ground_truth() -> dict:
    """Returns {func_name: [faulty_line, ...]}."""
    with open(GT_PATH) as f:
        data = json.load(f)
    result = {}
    for entry in data.get("programs", []):
        name = entry["file"].replace(".py", "")
        result[name] = entry.get("faulty_lines", [])
    return result


def _acc_from_csv(csv_path: str) -> dict:
    """Read rq1_localization.csv and compute Acc@1/3/5, Med.Rank, %Susp."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        return {}

    def _v(r, key):
        v = r.get(key, "N/A")
        return None if v == "N/A" else int(v)

    top1 = [_v(r, "top1_acc") for r in rows if _v(r, "top1_acc") is not None]
    top3 = [_v(r, "top3_acc") for r in rows if _v(r, "top3_acc") is not None]
    top5 = [_v(r, "top5_acc") for r in rows if _v(r, "top5_acc") is not None]
    pcts = [float(r["pct_suspicious"]) for r in rows if r.get("pct_suspicious") not in ("", "N/A")]
    ranks = sorted(int(r["best_rank"]) for r in rows
                   if r.get("best_rank") not in ("", "N/A", "None"))

    return {
        "acc1": sum(top1) / len(top1) if top1 else None,
        "acc3": sum(top3) / len(top3) if top3 else None,
        "acc5": sum(top5) / len(top5) if top5 else None,
        "median_rank": ranks[len(ranks) // 2] if ranks else None,
        "mean_pct_susp": sum(pcts) / len(pcts) if pcts else None,
        "n": len(rows),
    }


def _acc_from_semloc_dir(variant_dir: str) -> dict:
    """Read from a SemLoc results/ subdir (prefers results_cf_base/ then results/)."""
    for subdir in ("results_cf_base", "results"):
        csv_path = os.path.join(variant_dir, subdir, "rq1_localization.csv")
        if os.path.exists(csv_path):
            return _acc_from_csv(csv_path)
    return {}


def _acc_from_direct_fl(variant_dir: str) -> dict:
    """Aggregate from per-program JSON files in a semantic-indexing-disabled dir."""
    files = sorted(glob.glob(os.path.join(variant_dir, "*.json")))
    if not files:
        # Try direct_fl/ subdir
        files = sorted(glob.glob(os.path.join(variant_dir, "direct_fl", "*.json")))
    if not files:
        return {}

    # Skip aggregate.json
    files = [f for f in files if os.path.basename(f) != "aggregate.json"
             and os.path.basename(f) != "summary.csv"]

    top1, top3, top5 = [], [], []
    ranks = []
    for path in files:
        try:
            with open(path) as f:
                d = json.load(f)
        except Exception:
            continue
        if "top1_rate" in d:
            # per-program file from llm_direct_fl.py
            if d.get("top1_rate") is not None:
                top1.append(int(d["top1_rate"] > 0))
            if d.get("top3_rate") is not None:
                top3.append(int(d["top3_rate"] > 0))
            if d.get("top5_rate") is not None:
                top5.append(int(d["top5_rate"] > 0))
            br = d.get("best_rank_ever")
            if isinstance(br, int):
                ranks.append(br)

    return {
        "acc1": sum(top1) / len(top1) if top1 else None,
        "acc3": sum(top3) / len(top3) if top3 else None,
        "acc5": sum(top5) / len(top5) if top5 else None,
        "median_rank": sorted(ranks)[len(ranks) // 2] if ranks else None,
        "mean_pct_susp": None,
        "n": len(top1),
    }


def _acc_from_sbfl(variant_dir: str, formula: str, gt: dict) -> dict:
    """Compute Acc@1/3/5 from per-program SBFL/DD JSON files.

    Handles three file formats:
      - baselines.py output:  {"sbfl": {line_scores, pct_suspicious}, "dd": {minimal_lines, ...}}
      - tarantula output:     {line_scores, pct_suspicious}  (flat)
      - DD treatment:         uses dd.minimal_lines (unranked set of suspicious lines)
    """
    files = sorted(glob.glob(os.path.join(variant_dir, "*.json")))
    top1, top3, top5 = [], [], []
    pcts = []
    ranks = []

    for path in files:
        func = os.path.basename(path).replace(".json", "")
        faulty = gt.get(func, [])
        try:
            with open(path) as f:
                d = json.load(f)
        except Exception:
            continue

        if formula == "dd":
            # DD: minimal_lines is an unranked set; treat each as rank 1
            result = d.get("dd", {})
            minimal = result.get("minimal_lines", [])
            pct = result.get("pct_suspicious")
            if pct is not None:
                pcts.append(float(pct))
            if not faulty:
                continue
            hit = any(fl in minimal for fl in faulty)
            top1.append(1 if hit else 0)
            top3.append(1 if hit else 0)
            top5.append(1 if hit else 0)
            if hit:
                ranks.append(1)
        else:
            # SBFL: rank lines by score
            # Support both nested {"sbfl": {...}} and flat {line_scores, ...}
            if "sbfl" in d and isinstance(d["sbfl"], dict) and "line_scores" in d["sbfl"]:
                result = d["sbfl"]
            elif "line_scores" in d:
                result = d
            else:
                result = {}

            line_scores = result.get("line_scores", {})
            pct = result.get("pct_suspicious")
            if pct is not None:
                pcts.append(float(pct))

            ranked = sorted(line_scores.items(), key=lambda x: -float(x[1]))
            ranked_lines = [int(ln) for ln, _ in ranked]

            if not faulty:
                continue

            best_rank = None
            for fl in faulty:
                if fl in ranked_lines:
                    r = ranked_lines.index(fl) + 1
                    best_rank = r if best_rank is None else min(best_rank, r)

            if best_rank is not None:
                ranks.append(best_rank)
                top1.append(1 if best_rank <= 1 else 0)
                top3.append(1 if best_rank <= 3 else 0)
                top5.append(1 if best_rank <= 5 else 0)
            else:
                top1.append(0)
                top3.append(0)
                top5.append(0)

    n = len(top1)
    return {
        "acc1": sum(top1) / n if n else None,
        "acc3": sum(top3) / n if n else None,
        "acc5": sum(top5) / n if n else None,
        "median_rank": sorted(ranks)[len(ranks) // 2] if ranks else None,
        "mean_pct_susp": sum(pcts) / len(pcts) if pcts else None,
        "n": n,
    }


def _row(label: str, m: dict) -> str:
    n = m.get("n", "")
    n_str = f"({n})" if n else ""
    return (
        f"  {label:<42} "
        f"{_pct(m.get('acc1')):>8}  "
        f"{_pct(m.get('acc3')):>8}  "
        f"{_pct(m.get('acc5')):>8}  "
        f"{str(m.get('median_rank', 'N/A')):>10}  "
        f"{_fmt(m.get('mean_pct_susp')):>8}%  "
        f"{n_str}"
    )


# ---------------------------------------------------------------------------
# RQ1: Table 1
# ---------------------------------------------------------------------------

def print_rq1():
    gt = load_ground_truth()

    header = (
        f"  {'Configuration':<42} "
        f"{'Acc@1':>8}  "
        f"{'Acc@3':>8}  "
        f"{'Acc@5':>8}  "
        f"{'Med.Rank':>10}  "
        f"{'%Susp':>8}   "
        f"n"
    )
    sep = "  " + "-" * (len(header) - 2)

    print("=" * len(header))
    print("Table 1: Fault Localization Effectiveness (RQ1)")
    print("=" * len(header))
    print(header)
    print(sep)

    # SemLoc full system
    for label, dirname in [
        ("SemLoc  Claude T=0.0", "semloc_claude_T0.0"),
        ("SemLoc  Claude T=0.3", "semloc_claude_T0.3"),
        ("SemLoc  Claude T=0.8", "semloc_claude_T0.8"),
        ("SemLoc  Gemini T=0.0", "semloc_gemini_T0.0"),
        ("SemLoc  Gemini T=0.3", "semloc_gemini_T0.3"),
        ("SemLoc  Gemini T=0.8", "semloc_gemini_T0.8"),
    ]:
        d = os.path.join(RQ1_DIR, dirname)
        m = _acc_from_semloc_dir(d) if os.path.isdir(d) else {}
        print(_row(label, m))

    print(sep)

    # CF disabled
    for label, dirname in [
        ("CF disabled  Claude T=0.8", "cf_disabled_claude_T0.8"),
        ("CF disabled  Gemini T=0.8", "cf_disabled_gemini_T0.8"),
    ]:
        d = os.path.join(RQ1_DIR, dirname)
        m = _acc_from_csv(os.path.join(d, "rq1_localization.csv")) if os.path.isdir(d) else {}
        print(_row(label, m))

    print(sep)

    # Semantic indexing disabled
    for label, dirname in [
        ("Semantic indexing disabled  Claude", "semantic_indexing_disabled_claude"),
        ("Semantic indexing disabled  Gemini", "semantic_indexing_disabled_gemini"),
    ]:
        d = os.path.join(RQ1_DIR, dirname)
        m = _acc_from_direct_fl(d) if os.path.isdir(d) else {}
        print(_row(label, m))

    print(sep)

    # SBFL baselines
    for label, dirname, formula in [
        ("SBFL Ochiai",    "sbfl_ochiai",    "ochiai"),
        ("SBFL Tarantula", "sbfl_tarantula",  "tarantula"),
    ]:
        d = os.path.join(RQ1_DIR, dirname)
        m = _acc_from_sbfl(d, formula, gt) if os.path.isdir(d) else {}
        print(_row(label, m))

    # DD baseline
    d = os.path.join(RQ1_DIR, "dd")
    m = _acc_from_sbfl(d, "dd", gt) if os.path.isdir(d) else {}
    print(_row("Delta Debugging (DD)", m))

    print("=" * len(header))
    print()
    print("Result files:")
    print(f"  Per-configuration CSV:  results/RQ1/<config>/rq1_localization.csv")
    print(f"  Per-configuration JSON: results/RQ1/<config>/results/summary.json")
    print(f"                       or results/RQ1/<config>/results_cf_base/summary.json")
    print(f"  Big-table JSON:         results/RQ1/summary.json  (6 SemLoc variants)")


# ---------------------------------------------------------------------------
# RQ2: Constraint quality
# ---------------------------------------------------------------------------

def print_rq2():
    analyze_script = os.path.join(RQ2_DIR, "analyze_constraints.py")
    if os.path.exists(analyze_script):
        import subprocess
        subprocess.run(["python", analyze_script], check=False)
    else:
        print(f"[rq2] analyze_constraints.py not found at {analyze_script}")

    summary_path = os.path.join(RQ2_DIR, "results_cf_base", "summary.json")
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            d = json.load(f)
        r = d.get("rq1", {})
        print("\nCF-scored localization (pre-computed):")
        print(f"  Acc@1:   {_pct(r.get('top1_accuracy'))}")
        print(f"  Acc@3:   {_pct(r.get('top3_accuracy'))}")
        print(f"  %Susp:   {_fmt(r.get('mean_pct_suspicious'))}%")
        print(f"  n:       {d.get('n_programs')}")


# ---------------------------------------------------------------------------
# RQ3: BugsInPy
# ---------------------------------------------------------------------------

def print_rq3():
    files = glob.glob(os.path.join(RQ3_DIR, "*.json"))
    if not files:
        print(f"[rq3] No result files found in {RQ3_DIR}")
        return

    results = []
    for path in files:
        try:
            with open(path) as f:
                results.append(json.load(f))
        except Exception:
            continue

    n = len(results)

    def _semloc(r):
        s = r.get("semloc", {})
        return s if isinstance(s, dict) and "error" not in s else {}

    ran     = sum(1 for r in results if _semloc(r))
    primary = sum(1 for r in results if _semloc(r).get("cf_primary"))
    top1    = sum(1 for r in results if _semloc(r).get("top1"))
    top3    = sum(1 for r in results if _semloc(r).get("top3"))
    top5    = sum(1 for r in results if _semloc(r).get("top5"))

    print("=" * 60)
    print("Table: RQ3 — Real-World BugsInPy Evaluation")
    print("=" * 60)
    print(f"  Total bugs:          {n}  (SemLoc ran on {ran})")
    print(f"  CF Primary:          {primary}/{ran}  ({100*primary/ran:.1f}% of ran)" if ran else "  CF Primary: N/A")
    print(f"  Top-1 line correct:  {top1}/{ran}  ({100*top1/ran:.1f}%)" if ran else "  Top-1: N/A")
    print(f"  Top-3 line correct:  {top3}/{ran}  ({100*top3/ran:.1f}%)" if ran else "  Top-3: N/A")
    print(f"  Top-5 line correct:  {top5}/{ran}  ({100*top5/ran:.1f}%)" if ran else "  Top-5: N/A")
    print(f"\n  Result files: results/RQ3/bugsInPy_results/*.json")

    # Per-project summary
    projects = {}
    for r in results:
        bug_id = r.get("bug_id", "")
        proj = bug_id.rsplit("_", 1)[0] if "_" in bug_id else bug_id
        projects.setdefault(proj, []).append(r)

    if len(projects) > 1:
        print(f"\n  Per-project  (ran / CF-primary / top1):")
        for proj in sorted(projects):
            bugs = projects[proj]
            n_ran = sum(1 for r in bugs if _semloc(r))
            n_p   = sum(1 for r in bugs if _semloc(r).get("cf_primary"))
            n_t1  = sum(1 for r in bugs if _semloc(r).get("top1"))
            print(f"    {proj:<20}  {n_ran:>3}/{len(bugs):>3}  primary={n_p}  top1={n_t1}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Print SemLoc result tables")
    parser.add_argument("--rq1", action="store_true", help="Print RQ1 table (default)")
    parser.add_argument("--rq2", action="store_true", help="Print RQ2 constraint quality")
    parser.add_argument("--rq3", action="store_true", help="Print RQ3 BugsInPy summary")
    parser.add_argument("--all", action="store_true", help="Print all tables")
    args = parser.parse_args()

    if args.all or not (args.rq1 or args.rq2 or args.rq3):
        print_rq1()
    if args.rq2 or args.all:
        print_rq2()
    if args.rq3 or args.all:
        print_rq3()


if __name__ == "__main__":
    main()
