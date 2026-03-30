#!/usr/bin/env bash
# =============================================================================
# reproduce_rq2.sh — Reproduce RQ2: Semantic Indexing Analysis
# =============================================================================
#
# Two modes:
#
# MODE 1 (fast, default): Print constraint quality statistics from pre-computed
#   constraints/, violations/, scores/ data.  No LLM calls needed.
#   Pre-computed CF results are already in results/RQ2/claude_T0.8/results_cf_base/.
#
# MODE 2 (full): Re-run everything from scratch (constraint inference +
#   instrumentation + violation collection + CF scoring).  Needs LLM API.
#
# Usage:
#   source myconfig.sh
#   bash scripts/reproduce_rq2.sh          # MODE 1 (fast, no API calls)
#   bash scripts/reproduce_rq2.sh --full   # MODE 2 (full re-run, needs LLM API)
#
# The pre-computed results are in results/RQ2/claude_T0.8/.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC="$ARTIFACT_ROOT/src"
BENCHMARK="$ARTIFACT_ROOT/benchmark"
RQ2_DIR="$ARTIFACT_ROOT/results/RQ2/claude_T0.8"
WORKERS="${WORKERS:-8}"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-sonnet-4-6}"
FULL_RERUN=false

for arg in "$@"; do
    [ "$arg" = "--full" ] && FULL_RERUN=true
done

echo "============================================================"
echo "RQ2 Reproduction — Semantic Indexing Analysis"
echo "Mode: $([ "$FULL_RERUN" = true ] && echo 'FULL re-run' || echo 'fast (pre-computed data)')"
echo "============================================================"

if [ "$FULL_RERUN" = true ]; then
    echo ""
    echo "--- Full re-run: inference + instrumentation + violations + CF scoring ---"
    FULL_DIR="/tmp/semloc_rq2_full"
    mkdir -p "$FULL_DIR"

    # Link benchmark (absolute symlinks)
    [ -e "$FULL_DIR/programs"  ] || ln -s "$(realpath "$BENCHMARK/programs")"  "$FULL_DIR/programs"
    [ -e "$FULL_DIR/testcases" ] || ln -s "$(realpath "$BENCHMARK/testcases")" "$FULL_DIR/testcases"
    [ -e "$FULL_DIR/ground_truth.json" ] || ln -s "$(realpath "$BENCHMARK/ground_truth.json")" "$FULL_DIR/ground_truth.json"

    python "$SRC/run_eval.py" \
        --working-dir "$FULL_DIR" \
        --model "$CLAUDE_MODEL" \
        --temperature 0.8 \
        --workers "$WORKERS" \
        --steps 1,3,4,5,6,8 \
        --cf-on-base

    # Copy analysis script into the full run dir
    cp "$RQ2_DIR/analyze_constraints.py" "$FULL_DIR/"

    echo ""
    echo "--- Constraint quality statistics ---"
    python "$FULL_DIR/analyze_constraints.py" --dir "$FULL_DIR"
else
    echo ""
    echo "--- Constraint quality statistics (from pre-computed data) ---"
    python "$RQ2_DIR/analyze_constraints.py"

    echo ""
    echo "Pre-computed CF results: $RQ2_DIR/results_cf_base/summary.json"
    echo ""
    echo "To re-run CF scoring on pre-computed spectrum scores (requires LLM API):"
    echo "  # Link benchmark data"
    echo "  ln -sf \"\$(realpath benchmark/programs)\" results/RQ2/claude_T0.8/programs"
    echo "  ln -sf \"\$(realpath benchmark/testcases)\" results/RQ2/claude_T0.8/testcases"
    echo "  ln -sf \"\$(realpath benchmark/ground_truth.json)\" results/RQ2/claude_T0.8/ground_truth.json"
    echo "  # Run CF scoring only"
    echo "  python src/run_eval.py --working-dir results/RQ2/claude_T0.8 --steps 8 --cf-on-base \\"
    echo "    --model \$CLAUDE_MODEL --workers \$WORKERS"
fi

echo ""
echo "============================================================"
echo "RQ2 reproduction complete."
echo "============================================================"
