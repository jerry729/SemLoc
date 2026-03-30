#!/usr/bin/env bash
# =============================================================================
# reproduce_rq1.sh — Reproduce RQ1: Fault Localization Effectiveness
# =============================================================================
#
# Reproduces all configurations in Table 1 (fl.tex) of the paper:
#   - SemLoc (full system): Claude Sonnet 4.6 at T=0.0, 0.3, 0.8
#   - SemLoc (full system): Gemini 2.5 Pro at T=0.0, 0.3, 0.8
#   - CF reasoning disabled: Claude T=0.8, Gemini T=0.8
#   - Semantic indexing disabled: Claude, Gemini
#   - SBFL baselines (Ochiai, Tarantula) and Delta Debugging (DD)
#
# SETUP:
#   1. source myconfig.sh   (fill in API keys first)
#   2. Run from artifact root:  bash scripts/reproduce_rq1.sh
#
# Outputs go to /tmp/semloc_rq1/ by default.
# Set OUTPUT_DIR to a different path if desired.
#
# NOTE: Full reproduction requires LLM API access and takes several hours
# (constraint inference is the bottleneck: ~250 LLM calls per configuration).
# Pre-computed results are in results/RQ1/ if you want to skip inference.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC="$ARTIFACT_ROOT/src"
BENCHMARK="$ARTIFACT_ROOT/benchmark"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/semloc_rq1}"
WORKERS="${WORKERS:-8}"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-sonnet-4-6}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-pro}"

mkdir -p "$OUTPUT_DIR"
cd "$ARTIFACT_ROOT"

echo "============================================================"
echo "RQ1 Reproduction — SemLoc Fault Localization"
echo "Output: $OUTPUT_DIR"
echo "Workers: $WORKERS"
echo "============================================================"

# ---------------------------------------------------------------------------
# Helper: run the full SemLoc pipeline (steps 1,3,4,5,6,8 + CF on base)
# ---------------------------------------------------------------------------
run_semloc() {
    local label="$1"
    local model="$2"
    local temp="$3"
    local out_dir="$OUTPUT_DIR/$label"

    echo ""
    echo "--- SemLoc: $label (model=$model, T=$temp) ---"
    mkdir -p "$out_dir"

    # Link benchmark data into working dir
    [ -e "$out_dir/programs"  ] || ln -s "$(realpath "$BENCHMARK/programs")"  "$out_dir/programs"
    [ -e "$out_dir/testcases" ] || ln -s "$(realpath "$BENCHMARK/testcases")" "$out_dir/testcases"
    [ -e "$out_dir/ground_truth.json" ] || ln -s "$(realpath "$BENCHMARK/ground_truth.json")" "$out_dir/ground_truth.json"

    python "$SRC/run_eval.py" \
        --working-dir "$out_dir" \
        --model "$model" \
        --temperature "$temp" \
        --workers "$WORKERS" \
        --steps 1,3,4,5,6,8 \
        --cf-on-base

    echo "Results: $out_dir/results_cf_base/summary.json"
}

# ---------------------------------------------------------------------------
# Helper: run CF-disabled variant
# ---------------------------------------------------------------------------
run_semloc_cf_disabled() {
    local label="$1"
    local model="$2"
    local temp="$3"
    local out_dir="$OUTPUT_DIR/$label"

    echo ""
    echo "--- CF disabled: $label ---"
    mkdir -p "$out_dir"
    [ -e "$out_dir/programs"  ] || ln -s "$(realpath "$BENCHMARK/programs")"  "$out_dir/programs"
    [ -e "$out_dir/testcases" ] || ln -s "$(realpath "$BENCHMARK/testcases")" "$out_dir/testcases"
    [ -e "$out_dir/ground_truth.json" ] || ln -s "$(realpath "$BENCHMARK/ground_truth.json")" "$out_dir/ground_truth.json"

    python "$SRC/run_eval.py" \
        --working-dir "$out_dir" \
        --model "$model" \
        --temperature "$temp" \
        --workers "$WORKERS" \
        --steps 1,3,4,5,6,8 \
        --cf-disabled

    echo "Results: $out_dir/results_refined/summary.json"
}

# ---------------------------------------------------------------------------
# Helper: run semantic-indexing-disabled variant
# ---------------------------------------------------------------------------
run_semantic_indexing_disabled() {
    local label="$1"
    local model="$2"
    local out_dir="$OUTPUT_DIR/$label"

    echo ""
    echo "--- Semantic indexing disabled: $label ---"
    mkdir -p "$out_dir"
    [ -e "$out_dir/programs"  ] || ln -s "$(realpath "$BENCHMARK/programs")"  "$out_dir/programs"
    [ -e "$out_dir/testcases" ] || ln -s "$(realpath "$BENCHMARK/testcases")" "$out_dir/testcases"
    [ -e "$out_dir/ground_truth.json" ] || ln -s "$(realpath "$BENCHMARK/ground_truth.json")" "$out_dir/ground_truth.json"

    python "$SRC/run_eval.py" \
        --working-dir "$out_dir" \
        --model "$model" \
        --workers "$WORKERS" \
        --disable-semantic-index

    echo "Results: $out_dir/direct_fl/aggregate.json"
}

# ---------------------------------------------------------------------------
# Helper: run SBFL and DD baselines
# ---------------------------------------------------------------------------
run_baselines() {
    local out_dir="$OUTPUT_DIR/baselines"
    echo ""
    echo "--- SBFL (Ochiai, Tarantula) + DD baselines ---"
    mkdir -p "$out_dir"
    [ -L "$out_dir/programs"  ] || ln -s "$BENCHMARK/programs"  "$out_dir/programs"
    [ -L "$out_dir/testcases" ] || ln -s "$BENCHMARK/testcases" "$out_dir/testcases"

    # This runs both SBFL (Ochiai) and DD in parallel; writes per-program JSONs
    python "$SRC/baselines.py" "$out_dir" "$WORKERS"

    echo "Results: $out_dir/results/baselines/"
}

# ---------------------------------------------------------------------------
# Run all configurations
# ---------------------------------------------------------------------------

# SemLoc full system (6 configurations)
run_semloc "semloc_claude_T0.0" "$CLAUDE_MODEL" 0.0
run_semloc "semloc_claude_T0.3" "$CLAUDE_MODEL" 0.3
run_semloc "semloc_claude_T0.8" "$CLAUDE_MODEL" 0.8
run_semloc "semloc_gemini_T0.0" "$GEMINI_MODEL" 0.0
run_semloc "semloc_gemini_T0.3" "$GEMINI_MODEL" 0.3
run_semloc "semloc_gemini_T0.8" "$GEMINI_MODEL" 0.8

# CF reasoning disabled (2 configurations)
run_semloc_cf_disabled "cf_disabled_claude_T0.8" "$CLAUDE_MODEL" 0.8
run_semloc_cf_disabled "cf_disabled_gemini_T0.8" "$GEMINI_MODEL" 0.8

# Semantic indexing disabled (2 configurations)
run_semantic_indexing_disabled "semantic_indexing_disabled_claude" "$CLAUDE_MODEL"
run_semantic_indexing_disabled "semantic_indexing_disabled_gemini" "$GEMINI_MODEL"

# SBFL baselines + DD
run_baselines

echo ""
echo "============================================================"
echo "RQ1 reproduction complete."
echo "All results in: $OUTPUT_DIR"
echo "============================================================"
