#!/usr/bin/env python3
"""
llm_direct_fl.py — Direct LLM Fault Localization Baseline (RQ0 / reviewer ablation).

Asks an LLM to directly identify faulty line numbers given buggy source + test
results, WITHOUT any SemLoc constraint infrastructure.  Runs each program
multiple times (default N=5) to measure:

  - Top-k accuracy      (is the true faulty line in top-k predictions?)
  - Hallucination rate  (predicted lines that do not exist in source)
  - Consistency         (agreement across N independent runs)
  - Mean suspicion set  (how many lines does the LLM flag on average?)

The output is a JSON+CSV summary that can be included as a table column or
paragraph in the paper to answer: "Could you just ask the LLM directly?"

Usage:
    python llm_direct_fl.py [--working-dir example_pipeline] [--n-runs 5]
                            [--model gemini-2.5-pro] [--force]
    python llm_direct_fl.py --dry-run   # print prompts only, no API calls
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a fault localization expert. Given a buggy Python function and "
    "test failure information, identify the exact line number(s) that contain "
    "the fault. Be precise and return only what the schema requires."
)

_OUTPUT_SCHEMA = textwrap.dedent("""
Output ONLY valid JSON matching this schema — no prose, no markdown fences:

{
  "function_name": "<string>",
  "faulty_lines": [<integer>, ...],
  "explanation": "<one or two sentences>",
  "confidence": <float 0.0 to 1.0>
}

Rules:
- faulty_lines must list 1-indexed line numbers of the lines you believe are faulty.
- List up to 5 lines; order them from most to least suspicious.
- If you are uncertain, still provide your best guess — do NOT leave faulty_lines empty.
- confidence reflects your overall certainty.
""").strip()


_BUG_MARKER_RE = re.compile(r"\s*#.*\b(BUG|FIXME|HACK|bug|fixme)\b.*$")


def _strip_bug_markers(src: str) -> str:
    """Remove inline comments and standalone comment lines containing BUG/FIXME markers.

    Preserves line count so that line numbers in the prompt still match the
    original source (important for evaluating top-k accuracy against ground truth).
    Standalone comment-only lines are blanked; inline markers are stripped.
    """
    out = []
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#") and _BUG_MARKER_RE.search(stripped):
            # Standalone comment line — blank it to preserve line numbering
            out.append("")
        else:
            # Strip inline BUG marker from the end of a code line
            out.append(_BUG_MARKER_RE.sub("", line))
    return "\n".join(out)


def _numbered_source(src: str) -> str:
    """Return source with 1-indexed line numbers like a code editor."""
    lines = src.splitlines()
    width = len(str(len(lines)))
    return "\n".join(f"{i+1:>{width}}: {line}" for i, line in enumerate(lines))


def build_direct_fl_prompt(execution_result: Dict) -> str:
    """Build a direct fault localization prompt from source code only.

    BUG/FIXME markers are stripped from the source so the LLM must reason
    about the code itself rather than reading embedded hints.
    """
    fn_name = execution_result.get("target_function", "unknown")
    src_parts = execution_result.get("src_program", [])
    src = src_parts[0] if isinstance(src_parts, list) else src_parts
    src = _strip_bug_markers(src)

    lines = [
        f"Function under test: {fn_name}",
        "",
        "=== Source (with line numbers) ===",
        _numbered_source(src),
        "",
        _OUTPUT_SCHEMA,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM query helpers  (reuse from constraint_inference)
# ---------------------------------------------------------------------------

def _load_env() -> None:
    _env = Path(__file__).resolve().parent / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(_env, override=True)
    except ImportError:
        pass


def _strip_fences(text: str) -> str:
    text = text.strip()
    # If there's a ```json ... ``` block anywhere, extract its content
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    # Fallback: strip leading/trailing fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _query_openai(prompt: str, model: str, temperature: float = 0.0) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


def _query_gemini(prompt: str, model: str, temperature: float = 0.0) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("pip install google-genai")
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set in .env")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=temperature,
        ),
    )
    return response.text


def _query_claude_vertex(prompt: str, model: str, temperature: float = 0.0) -> str:
    """Query Claude via Anthropic Vertex AI (GCP)."""
    try:
        from anthropic import AnthropicVertex
    except ImportError:
        raise ImportError("pip install 'anthropic[vertex]'")
    _load_env()
    project_id = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
    region = os.environ.get("ANTHROPIC_VERTEX_REGION", "us-east5")
    if not project_id:
        raise EnvironmentError("ANTHROPIC_VERTEX_PROJECT_ID not set in .env")
    client = AnthropicVertex(project_id=project_id, region=region)
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        temperature=temperature,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _query_llm(prompt: str, model: str, temperature: float = 0.0) -> str:
    if model.startswith("gemini"):
        return _query_gemini(prompt, model, temperature)
    if model.startswith("claude"):
        return _query_claude_vertex(prompt, model, temperature)
    return _query_openai(prompt, model, temperature)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_fl_response(raw: str) -> Dict:
    """Parse LLM response into a structured dict; return error info on failure."""
    content = _strip_fences(raw)
    try:
        data = json.loads(content)
        lines = data.get("faulty_lines", [])
        if not isinstance(lines, list):
            lines = [lines] if isinstance(lines, int) else []
        return {
            "faulty_lines": [int(x) for x in lines if isinstance(x, (int, float, str)) and str(x).isdigit()],
            "explanation": data.get("explanation", ""),
            "confidence": float(data.get("confidence", 0.0)),
            "parse_ok": True,
            "raw": raw,
        }
    except Exception as e:
        # Try to extract line numbers with regex as fallback
        nums = re.findall(r'"faulty_lines"\s*:\s*\[([^\]]*)\]', content)
        fallback: List[int] = []
        if nums:
            for token in nums[0].split(","):
                token = token.strip()
                if token.isdigit():
                    fallback.append(int(token))
        return {
            "faulty_lines": fallback,
            "explanation": f"[parse error: {e}]",
            "confidence": 0.0,
            "parse_ok": False,
            "raw": raw,
        }


# ---------------------------------------------------------------------------
# Per-program evaluation
# ---------------------------------------------------------------------------

def _count_source_lines(src: str) -> int:
    return len(src.splitlines())


def evaluate_single_run(
    predicted: List[int],
    faulty_lines: List[int],
    total_source_lines: int,
) -> Dict:
    """Compute accuracy + hallucination metrics for one run."""
    valid_range = set(range(1, total_source_lines + 1))
    hallucinated = [ln for ln in predicted if ln not in valid_range]
    valid_preds = [ln for ln in predicted if ln in valid_range]

    faulty_set = set(faulty_lines)
    top1 = bool(valid_preds) and valid_preds[0] in faulty_set
    top3 = any(ln in faulty_set for ln in valid_preds[:3])
    top5 = any(ln in faulty_set for ln in valid_preds[:5])
    any_correct = any(ln in faulty_set for ln in valid_preds)

    best_rank: Optional[int] = None
    for i, ln in enumerate(valid_preds):
        if ln in faulty_set:
            best_rank = i + 1
            break

    return {
        "predicted": predicted,
        "valid_preds": valid_preds,
        "hallucinated": hallucinated,
        "n_hallucinated": len(hallucinated),
        "top1": top1,
        "top3": top3,
        "top5": top5,
        "any_correct": any_correct,
        "best_rank": best_rank,
        "n_predicted": len(predicted),
    }


def run_direct_fl(
    execution_result: Dict,
    faulty_lines: List[int],
    model: str,
    n_runs: int = 5,
    dry_run: bool = False,
    temperature: float = 0.0,
) -> Dict:
    """Run direct LLM FL N times and aggregate metrics."""
    fn_name = execution_result.get("target_function", "unknown")
    src_parts = execution_result.get("src_program", [])
    src = src_parts[0] if isinstance(src_parts, list) else src_parts
    total_lines = _count_source_lines(src)

    prompt = build_direct_fl_prompt(execution_result)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"PROMPT for {fn_name}:")
        print(prompt[:2000])
        return {"function": fn_name, "dry_run": True}

    raw_runs: List[Dict] = []
    for i in range(n_runs):
        print(f"  [{fn_name}] run {i+1}/{n_runs}…", end=" ", flush=True)
        try:
            raw = _query_llm(prompt, model, temperature=temperature)
            parsed = parse_fl_response(raw)
            metrics = evaluate_single_run(parsed["faulty_lines"], faulty_lines, total_lines)
            raw_runs.append({**parsed, **metrics, "run": i + 1})
            top1_str = "✓" if metrics["top1"] else ("~" if metrics["any_correct"] else "✗")
            hall_str = f"H{metrics['n_hallucinated']}" if metrics["n_hallucinated"] else ""
            print(f"{top1_str} pred={metrics['predicted']} {hall_str}")
        except Exception as e:
            print(f"ERROR: {e}")
            raw_runs.append({"run": i + 1, "error": str(e), "faulty_lines": [], "top1": False, "top3": False, "top5": False, "any_correct": False, "n_hallucinated": 0, "best_rank": None, "n_predicted": 0})

    # Aggregate
    n_valid = len([r for r in raw_runs if "error" not in r])
    top1_rate = sum(r.get("top1", False) for r in raw_runs) / n_runs
    top3_rate = sum(r.get("top3", False) for r in raw_runs) / n_runs
    top5_rate = sum(r.get("top5", False) for r in raw_runs) / n_runs
    any_correct_rate = sum(r.get("any_correct", False) for r in raw_runs) / n_runs
    hall_rate = sum(r.get("n_hallucinated", 0) > 0 for r in raw_runs) / n_runs
    mean_n_predicted = (
        sum(r.get("n_predicted", 0) for r in raw_runs) / n_valid if n_valid else 0
    )

    # Consistency: fraction of runs that agree on top-1 prediction
    top1_preds = [r["valid_preds"][0] for r in raw_runs if r.get("valid_preds")]
    if top1_preds:
        most_common = max(set(top1_preds), key=top1_preds.count)
        consistency = top1_preds.count(most_common) / n_runs
        modal_top1 = most_common
    else:
        consistency = 0.0
        modal_top1 = None

    # Best rank across runs (optimistic)
    best_ranks = [r["best_rank"] for r in raw_runs if r.get("best_rank") is not None]
    best_rank_ever = min(best_ranks) if best_ranks else None

    return {
        "function": fn_name,
        "n_runs": n_runs,
        "n_valid_runs": n_valid,
        "faulty_lines_gt": faulty_lines,
        "total_source_lines": total_lines,
        # Per-run details
        "runs": raw_runs,
        # Aggregated metrics
        "top1_rate": round(top1_rate, 3),
        "top3_rate": round(top3_rate, 3),
        "top5_rate": round(top5_rate, 3),
        "any_correct_rate": round(any_correct_rate, 3),
        "hallucination_rate": round(hall_rate, 3),
        "consistency": round(consistency, 3),
        "modal_top1": modal_top1,
        "best_rank_ever": best_rank_ever,
        "mean_n_predicted": round(mean_n_predicted, 1),
    }


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

def _ensure_execution_data(working_dir: str) -> str:
    """Generate execution data if execution/ dir is empty; return exec_dir path."""
    exec_dir = os.path.join(working_dir, "execution")
    os.makedirs(exec_dir, exist_ok=True)

    if list(Path(exec_dir).glob("*.json")):
        return exec_dir  # already populated

    programs_dir = os.path.join(working_dir, "programs")
    test_dir = os.path.join(working_dir, "testcases")
    json_dir = os.path.join(working_dir, "json_testcases")

    if not os.path.isdir(programs_dir) or not os.path.isdir(test_dir):
        return exec_dir  # nothing to generate

    print("[direct_fl] execution/ is empty — running tests to generate execution data…")
    try:
        from constraint_inference import run_pytest
        results = run_pytest(
            test_dir=test_dir,
            test_file=None,
            json_dir=json_dir if os.path.isdir(json_dir) else None,
            src_dir=programs_dir,
        )
        for tr in results:
            func_name = tr["target_function"]
            save_path = os.path.join(exec_dir, f"{func_name}.json")
            with open(save_path, "w") as f:
                json.dump(tr, f, indent=2)
            print(f"[direct_fl]   generated {save_path}")
    except Exception as e:
        print(f"[direct_fl] WARNING: could not auto-generate execution data: {e}")

    return exec_dir


def run_experiment(
    working_dir: str,
    n_runs: int = 5,
    model: str = "gemini-2.5-pro",
    force: bool = False,
    dry_run: bool = False,
    temperature: float = 0.0,
    workers: int = 8,
) -> None:
    import concurrent.futures
    import threading

    _load_env()

    exec_dir = _ensure_execution_data(working_dir)
    gt_path = os.path.join(working_dir, "ground_truth.json")
    out_dir = os.path.join(working_dir, "direct_fl")
    os.makedirs(out_dir, exist_ok=True)

    # Load ground truth
    gt_by_file: Dict[str, List[int]] = {}
    if os.path.exists(gt_path):
        with open(gt_path) as f:
            gt = json.load(f)
        for entry in gt.get("programs", []):
            fname = entry["file"].replace(".py", "")
            gt_by_file[fname] = entry.get("faulty_lines", [])
    else:
        print(f"[direct_fl] WARNING: no ground_truth.json at {gt_path}")

    all_results: Dict[str, Dict] = {}
    _lock = threading.Lock()

    json_files = sorted(Path(exec_dir).glob("*.json"))

    def _do_one(json_file):
        func_name = json_file.stem
        out_path = os.path.join(out_dir, f"{func_name}.json")

        if not force and os.path.exists(out_path) and not dry_run:
            print(f"[direct_fl] {func_name}: loading cached results")
            with open(out_path) as f:
                result = json.load(f)
            with _lock:
                all_results[func_name] = result
            return

        faulty_lines = gt_by_file.get(func_name, [])
        if not faulty_lines:
            print(f"[direct_fl] {func_name}: no ground truth, skipping")
            return

        with open(json_file) as f:
            exec_result = json.load(f)

        print(f"[direct_fl] {func_name}: ground truth lines={faulty_lines}")
        result = run_direct_fl(exec_result, faulty_lines, model, n_runs, dry_run,
                               temperature=temperature)

        if not dry_run:
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            with _lock:
                all_results[func_name] = result

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(_do_one, json_files))

    if dry_run or not all_results:
        return

    # Build summary CSV
    rows = []
    for func_name, r in sorted(all_results.items()):
        rows.append({
            "function": func_name,
            "n_runs": r["n_runs"],
            "faulty_lines_gt": str(r["faulty_lines_gt"]),
            "top1_rate": r["top1_rate"],
            "top3_rate": r["top3_rate"],
            "top5_rate": r["top5_rate"],
            "any_correct_rate": r["any_correct_rate"],
            "hallucination_rate": r["hallucination_rate"],
            "consistency": r["consistency"],
            "modal_top1": r["modal_top1"],
            "best_rank_ever": r.get("best_rank_ever", "N/A"),
            "mean_n_predicted": r["mean_n_predicted"],
        })

    csv_path = os.path.join(out_dir, "summary.csv")
    if rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    # Aggregate
    n = len(rows)
    if n:
        mean_top1 = sum(r["top1_rate"] for r in rows) / n
        mean_top3 = sum(r["top3_rate"] for r in rows) / n
        mean_hall = sum(r["hallucination_rate"] for r in rows) / n
        mean_cons = sum(r["consistency"] for r in rows) / n
        mean_any  = sum(r["any_correct_rate"] for r in rows) / n

        summary = {
            "model": model,
            "n_programs": n,
            "n_runs_per_program": n_runs,
            "aggregate": {
                "mean_top1_accuracy": round(mean_top1, 3),
                "mean_top3_accuracy": round(mean_top3, 3),
                "mean_any_correct": round(mean_any, 3),
                "mean_hallucination_rate": round(mean_hall, 3),
                "mean_consistency": round(mean_cons, 3),
            },
            "per_program": {
                r["function"]: {
                    "top1": r["top1_rate"],
                    "top3": r["top3_rate"],
                    "hall": r["hallucination_rate"],
                    "cons": r["consistency"],
                }
                for r in rows
            },
        }

        summary_path = os.path.join(out_dir, "aggregate.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n[direct_fl] === Aggregate Results ({model}, {n_runs} runs each) ===")
        print(f"  Programs:          {n}")
        print(f"  Top-1 accuracy:    {mean_top1:.1%}")
        print(f"  Top-3 accuracy:    {mean_top3:.1%}")
        print(f"  Any correct:       {mean_any:.1%}")
        print(f"  Hallucination:     {mean_hall:.1%}  (runs with ≥1 non-existent line)")
        print(f"  Consistency:       {mean_cons:.1%}  (runs agreeing on top-1 prediction)")
        print(f"\n  CSV:  {csv_path}")
        print(f"  JSON: {summary_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Direct LLM fault localization baseline for SemLoc comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          # Run 5 times per program with Gemini
          python llm_direct_fl.py --working-dir example_pipeline --n-runs 5

          # Dry run: print prompts only (no API calls)
          python llm_direct_fl.py --dry-run

          # Force re-run (ignore cached results)
          python llm_direct_fl.py --force --n-runs 3
        """),
    )
    parser.add_argument("--working-dir", default="./example_pipeline", metavar="DIR",
                        help="Pipeline working directory (must contain execution/ and ground_truth.json)")
    parser.add_argument("--n-runs", type=int, default=1,
                        help="Number of independent LLM runs per program (default: 5)")
    parser.add_argument("--model", default="gemini-2.5-pro",
                        help="LLM model (e.g. gemini-2.5-pro, gpt-4o)")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if cached results exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts only, no API calls")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="LLM temperature (default: 0.0)")
    parser.add_argument("--workers", type=int, default=8,
                        help="Parallel workers for LLM queries (default: 8)")
    args = parser.parse_args()

    run_experiment(
        working_dir=args.working_dir,
        n_runs=args.n_runs,
        model=args.model,
        force=args.force,
        dry_run=args.dry_run,
        temperature=args.temperature,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
