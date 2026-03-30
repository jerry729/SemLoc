#!/usr/bin/env bash
# =============================================================================
# reproduce_rq3.sh — Reproduce RQ3: Real-World BugsInPy Evaluation
# =============================================================================
#
# Runs SemLoc on a specified BugsInPy project (or a single bug).
# Pre-computed results for all 463 bugs are in results/RQ3/bugsInPy_results/.
#
# PREREQUISITES:
#   - Internet access (to clone project repos from GitHub)
#   - Git
#   - LLM API keys (set in config.sh)
#
# Usage:
#   source myconfig.sh
#
#   # Run all bugs in a project
#   bash scripts/reproduce_rq3.sh --project pandas
#
#   # Run a single bug
#   bash scripts/reproduce_rq3.sh --bug pandas_1 \
#       --function "pandas.core.dtypes.common.is_string_dtype"
#
#   # Run all projects (SLOW — clones many large repos)
#   bash scripts/reproduce_rq3.sh --all
#
# Output: results/RQ3/reproduce/<bug_id>.json
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC="$ARTIFACT_ROOT/src"
PRECOMPUTED="$ARTIFACT_ROOT/results/RQ3/bugsInPy_results"
WORKDIR="${WORKDIR:-/tmp/bip_checkouts}"
OUT_DIR="$ARTIFACT_ROOT/results/RQ3/reproduce"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-sonnet-4-6}"
WORKERS="${WORKERS:-4}"

# BugsInPy projects in the evaluation
ALL_PROJECTS=(
    PySnooper ansible black cookiecutter fastapi httpie keras luigi
    matplotlib pandas sanic scrapy spacy thefuck tornado youtube-dl
)

mkdir -p "$OUT_DIR"

usage() {
    echo "Usage: $0 [--project <name>] [--bug <bug_id> --function <fn>] [--all]"
    echo "  --project pandas      Run all bugs in the pandas project"
    echo "  --bug pandas_1 --function 'pandas.core.dtypes.common.is_string_dtype'"
    echo "  --all                 Run all projects (very slow)"
    exit 1
}

PROJECT=""
BUG_ID=""
FUNCTION=""
RUN_ALL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project) PROJECT="$2"; shift 2 ;;
        --bug)     BUG_ID="$2";  shift 2 ;;
        --function) FUNCTION="$2"; shift 2 ;;
        --all)     RUN_ALL=true; shift ;;
        *) usage ;;
    esac
done

run_bug() {
    local bug_id="$1"
    local function_name="$2"
    local out="$OUT_DIR/${bug_id}.json"

    if [ -f "$out" ]; then
        echo "[SKIP] $bug_id (already done)"
        return
    fi

    echo "[RUN] $bug_id — $function_name"

    python "$SRC/bip_runner.py" checkout-and-run "$bug_id" \
        --function "$function_name" \
        --workdir "$WORKDIR" \
        --out "$out" \
        --model "$CLAUDE_MODEL" \
        || echo "[WARN] $bug_id failed"
}

get_function_from_precomputed() {
    local bug_id="$1"
    local json_path="$PRECOMPUTED/${bug_id}.json"
    if [ -f "$json_path" ]; then
        python3 -c "
import json, sys
d = json.load(open('$json_path'))
fn = d.get('function', '') or d.get('predicted_function', '')
print(fn)
" 2>/dev/null || echo ""
    fi
}

run_project() {
    local project="$1"
    echo ""
    echo "=== Project: $project ==="

    # Find all pre-computed bugs for this project
    for json_path in "$PRECOMPUTED"/${project}_*.json; do
        [ -f "$json_path" ] || continue
        local bug_id
        bug_id=$(basename "$json_path" .json)
        local fn
        fn=$(get_function_from_precomputed "$bug_id")
        if [ -z "$fn" ]; then
            echo "[SKIP] $bug_id — no function name in pre-computed result"
            continue
        fi
        run_bug "$bug_id" "$fn"
    done
}

if [ -n "$BUG_ID" ] && [ -n "$FUNCTION" ]; then
    run_bug "$BUG_ID" "$FUNCTION"
elif [ -n "$PROJECT" ]; then
    run_project "$PROJECT"
elif [ "$RUN_ALL" = true ]; then
    for proj in "${ALL_PROJECTS[@]}"; do
        run_project "$proj"
    done
else
    echo "Pre-computed results: $PRECOMPUTED ($(ls "$PRECOMPUTED" | wc -l) bugs)"
    echo "To reproduce, specify --project, --bug, or --all."
    echo ""
    usage
fi

echo ""
echo "Results in: $OUT_DIR"
echo ""

# Print aggregate summary over reproduced results
if ls "$OUT_DIR"/*.json &>/dev/null; then
    python3 - "$OUT_DIR" <<'PYEOF'
import json, glob, sys, os
out_dir = sys.argv[1]
files = glob.glob(os.path.join(out_dir, "*.json"))
total = len(files)
top1 = top3 = top5 = cf_primary = 0
for f in files:
    d = json.load(open(f))
    if d.get("top1"): top1 += 1
    if d.get("top3"): top3 += 1
    if d.get("top5"): top5 += 1
    if d.get("cf_primary"): cf_primary += 1
print(f"=== RQ3 Summary ({total} bugs reproduced) ===")
print(f"  Top-1: {top1}/{total} ({100*top1/total:.1f}%)")
print(f"  Top-3: {top3}/{total} ({100*top3/total:.1f}%)")
print(f"  Top-5: {top5}/{total} ({100*top5/total:.1f}%)")
print(f"  CF Primary: {cf_primary}/{total} ({100*cf_primary/total:.1f}%)")
print(f"  Per-bug details: {out_dir}/<bug_id>.json")
PYEOF
fi
