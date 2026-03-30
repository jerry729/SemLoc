"""
spectrum.py — Violation matrix construction and suspiciousness scoring.

Usage:
    from spectrum import load_violations, deduplicate_records, group_by_sut, build_matrix, score_constraints, attribute_to_statements

Pipeline (combined JSONL with multiple SUTs):
    all_records = load_violations(".pytest_cache/cbfl/cbfl_violations.jsonl")
    records = deduplicate_records(all_records)
    by_sut = group_by_sut(records)
    sut_records = by_sut["split_escaped"]
    _, constraints = parse_constraints(open("constraints/split_escaped.json").read())
    vm = build_matrix(sut_records, [c.cid for c in constraints], sut="split_escaped")
    scores = score_constraints(vm)
    line_scores = attribute_to_statements(scores, constraints, open("programs/split_escaped.py").read())
    print(rank_lines(line_scores))
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from instrumentation import (
    Constraint,
    TSFunctionIndex,
    iter_stmt_contexts,
    _stmt_assigns_to_var,
    _stmt_uses_var,
    _is_return_stmt,
    _is_stmt_loop,
    _stmt_line_no,
    _parse_ssa_name,
    _find_defs_of_base,
    _find_subscript_mutations_of_base,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class TestRecord:
    nodeid: str
    outcome: str  # "passed" | "failed" | "skipped"
    duration: float
    violations: List[Dict]  # [{"sut": str, "cid": str, "reason": str}]
    longrepr: Optional[str]


@dataclass
class ViolationMatrix:
    records: List[TestRecord]       # active records (passing + failing, no skipped)
    cids: List[str]                 # ordered constraint IDs
    matrix: List[List[bool]]        # matrix[i][j] = True if record i violated cid j
    passing: List[TestRecord]
    failing: List[TestRecord]


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load_violations(jsonl_path: str) -> List[TestRecord]:
    """Parse a CBFL violations JSONL report into TestRecord objects."""
    records: List[TestRecord] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            records.append(
                TestRecord(
                    nodeid=d["nodeid"],
                    outcome=d["outcome"],
                    duration=d.get("duration", 0.0),
                    violations=d.get("violations", []),
                    longrepr=d.get("longrepr"),
                )
            )
    return records


def deduplicate_records(records: List[TestRecord]) -> List[TestRecord]:
    """Remove duplicate runs of the same test, keeping only the last occurrence.

    When pytest runs without clearing the cache, the JSONL accumulates multiple
    runs of the same test. The last run reflects the most recent state.
    """
    seen: Dict[str, TestRecord] = {}
    for r in records:
        seen[r.nodeid] = r  # last write wins
    return list(seen.values())


def group_by_sut(records: List[TestRecord]) -> Dict[str, List[TestRecord]]:
    """Group test records by SUT (program under test).

    SUT is extracted from the ``sut`` field of each violation entry.  Records
    with no violations are assigned to the SUT associated with their test file
    (inferred from other records in the same file that *do* have violations).
    Records whose SUT cannot be inferred are placed under the key ``"unknown"``.
    """
    # Build test-file → sut mapping from records that carry violations.
    file_to_sut: Dict[str, str] = {}
    for r in records:
        if r.violations:
            test_file = r.nodeid.split("::")[0]
            # Take the first sut seen for this file (typically only one per file).
            sut = r.violations[0]["sut"]
            file_to_sut.setdefault(test_file, sut)

    groups: Dict[str, List[TestRecord]] = {}
    for r in records:
        test_file = r.nodeid.split("::")[0]
        if r.violations:
            sut = r.violations[0]["sut"]
        else:
            sut = file_to_sut.get(test_file, "unknown")
        groups.setdefault(sut, []).append(r)

    return groups


# ---------------------------------------------------------------------------
# Matrix construction
# ---------------------------------------------------------------------------


def build_matrix(
    records: List[TestRecord],
    cids: List[str],
    sut: Optional[str] = None,
) -> ViolationMatrix:
    """Build a violation matrix from test records and an ordered list of constraint IDs.

    Args:
        records: Test records (typically already filtered to a single SUT via
                 ``group_by_sut``).
        cids: Ordered list of constraint IDs that form the matrix columns.
        sut: When provided, only violations whose ``sut`` field matches are
             counted.  This prevents CID name collisions when the JSONL contains
             data from multiple programs.
    """
    passing = [r for r in records if r.outcome == "passed"]
    failing = [r for r in records if r.outcome == "failed"]
    active = passing + failing  # skip "skipped" tests

    matrix: List[List[bool]] = []
    for r in active:
        if sut is not None:
            violated = {v["cid"] for v in r.violations if v.get("sut") == sut}
        else:
            violated = {v["cid"] for v in r.violations}
        matrix.append([cid in violated for cid in cids])

    return ViolationMatrix(
        records=active,
        cids=cids,
        matrix=matrix,
        passing=passing,
        failing=failing,
    )


# ---------------------------------------------------------------------------
# Scoring formulas
# ---------------------------------------------------------------------------


def ochiai(ef: int, nf: int, ep: int) -> float:
    """Ochiai suspiciousness: ef / sqrt(|T-| * (ef + ep))."""
    denom = math.sqrt((ef + nf) * (ef + ep))
    return ef / denom if denom > 0 else 0.0


def tarantula(ef: int, nf: int, ep: int, np: int) -> float:
    """Tarantula suspiciousness score."""
    if ef + nf == 0:
        return 0.0
    fail_rate = ef / (ef + nf)
    pass_rate = ep / (ep + np) if (ep + np) > 0 else 0.0
    denom = fail_rate + pass_rate
    return fail_rate / denom if denom > 0 else 0.0


def score_constraints(vm: ViolationMatrix) -> Dict[str, Dict]:
    """
    Compute ef, ep, nf, np and ochiai/tarantula scores for each constraint.

    Returns a dict: cid -> {"ef", "ep", "nf", "np", "ochiai", "tarantula"}
    """
    n_passing = len(vm.passing)
    n_failing = len(vm.failing)

    scores: Dict[str, Dict] = {}
    for j, cid in enumerate(vm.cids):
        ef = sum(
            1
            for i, r in enumerate(vm.records)
            if r.outcome == "failed" and vm.matrix[i][j]
        )
        ep = sum(
            1
            for i, r in enumerate(vm.records)
            if r.outcome == "passed" and vm.matrix[i][j]
        )
        nf = n_failing - ef
        np_ = n_passing - ep

        scores[cid] = {
            "ef": ef,
            "ep": ep,
            "nf": nf,
            "np": np_,
            "ochiai": ochiai(ef, nf, ep),
            "tarantula": tarantula(ef, nf, ep, np_),
        }
    return scores


# ---------------------------------------------------------------------------
# Line attribution
# ---------------------------------------------------------------------------


def find_anchor_lines(constraint: Constraint, src: str) -> List[int]:
    """
    Return source line numbers (1-indexed) where this constraint's check is inserted.

    Uses the same logic as the instrumentation handlers.
    """
    try:
        idx = TSFunctionIndex(src, constraint.fn_name)
    except Exception:
        return []

    region = constraint.region
    anchor = constraint.anchor
    lines: List[int] = []

    if region == "ENTRY":
        stmts = idx.stmts
        if stmts:
            lines.append(_stmt_line_no(stmts[0]))

    elif region in ("ANY_RETURN", "EXIT"):
        for ctx in iter_stmt_contexts(idx):
            if _is_return_stmt(ctx.stmt):
                lines.append(_stmt_line_no(ctx.stmt))

    elif region == "AFTER_DEF":
        var = anchor.get("var", "")
        if var:
            base, ver = _parse_ssa_name(var)
            all_defs = _find_defs_of_base(idx, base)
            if ver > 0 and ver > len(all_defs):
                target = [all_defs[-1]] if all_defs else _find_subscript_mutations_of_base(idx, base)
            elif ver > 0:
                target = [all_defs[ver - 1]]
            else:
                target = all_defs or _find_subscript_mutations_of_base(idx, base)
            for stmt in target:
                lines.append(_stmt_line_no(stmt))

    elif region == "BEFORE_USE":
        var = anchor.get("var", "")
        if var:
            base, _ = _parse_ssa_name(var)
            for ctx in iter_stmt_contexts(idx):
                if _stmt_uses_var(ctx.stmt, base):
                    lines.append(_stmt_line_no(ctx.stmt))

    elif region == "LOOP_HEAD":
        for ctx in iter_stmt_contexts(idx):
            if _is_stmt_loop(ctx.stmt):
                lines.append(_stmt_line_no(ctx.stmt))

    elif region == "LOOP_TAIL":
        loop_id = anchor.get("loop_id")
        from instrumentation import _collect_all_loops_in_function, _block_statements, _immediate_block_children
        all_loops = _collect_all_loops_in_function(idx)
        if loop_id is not None:
            target = [all_loops[int(loop_id) - 1]] if 1 <= int(loop_id) <= len(all_loops) else []
        else:
            target = all_loops
        for loop_node in target:
            body = _immediate_block_children(loop_node)
            if body is None:
                lines.append(_stmt_line_no(loop_node))
                continue
            body_stmts = _block_statements(body)
            if body_stmts:
                lines.append(_stmt_line_no(body_stmts[-1]))
            else:
                lines.append(_stmt_line_no(loop_node))

    elif region == "ON_EXIT":
        # Attribute to the last statement(s) before implicit return
        from instrumentation import _block_statements, _immediate_block_children
        block_stmts = idx.stmts
        if block_stmts:
            last = block_stmts[-1]
            if _is_return_stmt(last):
                lines.append(_stmt_line_no(last))
            else:
                # For implicit return: last stmt (or last nested stmt) is the anchor
                body = _immediate_block_children(last)
                if body:
                    inner = _block_statements(body)
                    if inner:
                        lines.append(_stmt_line_no(inner[-1]))
                        for s in inner:
                            lines.append(_stmt_line_no(s))
                    else:
                        lines.append(_stmt_line_no(last))
                else:
                    lines.append(_stmt_line_no(last))
        # Also include explicit returns
        for ctx in iter_stmt_contexts(idx):
            if _is_return_stmt(ctx.stmt):
                lines.append(_stmt_line_no(ctx.stmt))

    elif region == "LINE":
        # Anchor is directly a line number
        target_line = anchor.get("line")
        if isinstance(target_line, int):
            lines.append(target_line)

    elif region == "AFTER_BRANCH":
        # Attribute to the if_line itself (the if-statement's start line)
        if_line = anchor.get("if_line")
        if isinstance(if_line, int):
            lines.append(if_line)

    return sorted(set(lines))


# Granularity weights: fine-grained regions that pinpoint specific statements
# get full weight; coarse regions (ENTRY/ANY_RETURN) that only confirm the
# function is wrong get a reduced weight so they don't drown precise signals.
_GRANULARITY_WEIGHT: Dict[str, float] = {
    "LINE":         0.6,   # line-number hint; reduced weight since LLM is ~10% accurate
    "AFTER_BRANCH": 1.0,   # end of if/else branch — precise
    "AFTER_DEF":    1.0,
    "BEFORE_USE":   1.0,
    "LOOP_TAIL":    0.9,
    "LOOP_HEAD":    0.9,
    "AFTER_CALL":   0.9,
    "ON_EXIT":      0.5,
    "EXIT":         0.3,
    "ANY_RETURN":   0.3,
    "ENTRY":        0.2,
}


def attribute_to_statements(
    scores: Dict[str, Dict],
    constraints: List[Constraint],
    src: str,
    formula: str = "ochiai",
) -> Dict[int, float]:
    """
    Map constraint suspiciousness scores to source line numbers.

    Each line gets the maximum weighted score (by ``formula``) of any constraint
    anchored there.  Fine-grained regions (AFTER_DEF, BEFORE_USE, LOOP_TAIL)
    receive full weight; coarse regions (ENTRY, ANY_RETURN) are down-weighted.

    Args:
        formula: suspiciousness formula to use — ``"ochiai"`` or ``"tarantula"``.

    Returns: {line_number: weighted_max_score}
    """
    line_scores: Dict[int, float] = {}
    c_by_id = {c.cid: c for c in constraints}

    # Proximity decay for LINE constraints (LLM fault_line estimates are often
    # off by a few lines; spread credit to neighbours so nearby correct lines
    # still get boosted even when the prediction isn't exact).
    _LINE_PROXIMITY: List[tuple] = [(1, 0.55), (-1, 0.55), (2, 0.25), (-2, 0.25)]

    for cid, s in scores.items():
        c = c_by_id.get(cid)
        if c is None:
            continue
        score = s.get(formula, s.get("ochiai", 0.0))
        if score == 0.0:
            continue
        weight = _GRANULARITY_WEIGHT.get(c.region, 1.0)
        weighted = score * weight
        for ln in find_anchor_lines(c, src):
            line_scores[ln] = max(line_scores.get(ln, 0.0), weighted)

        # For LINE constraints also credit neighboring lines with decaying weight
        if c.region == "LINE":
            target = c.anchor.get("line")
            if isinstance(target, int):
                for offset, prox_factor in _LINE_PROXIMITY:
                    nb = target + offset
                    if nb > 0:
                        nb_score = score * weight * prox_factor
                        line_scores[nb] = max(line_scores.get(nb, 0.0), nb_score)

    return line_scores


# ---------------------------------------------------------------------------
# Ranking helpers
# ---------------------------------------------------------------------------


def rank_constraints(
    scores: Dict[str, Dict], formula: str = "ochiai"
) -> List[Tuple[str, float]]:
    """Return (cid, score) pairs sorted descending by suspiciousness."""
    return sorted(
        [(cid, s[formula]) for cid, s in scores.items()],
        key=lambda x: x[1],
        reverse=True,
    )


def rank_lines(line_scores: Dict[int, float]) -> List[Tuple[int, float]]:
    """Return (line_no, score) pairs sorted descending."""
    return sorted(line_scores.items(), key=lambda x: x[1], reverse=True)


def apply_fault_line_prior(
    line_scores: Dict[int, float],
    fault_line: Optional[int],
    prior_weight: float = 1.2,
) -> Dict[int, float]:
    """
    Boost the LLM's fault_line prediction so it ranks #1 unless runtime
    evidence contradicts it.

    The LLM's fault_line (42% accurate with absolute line numbers) is more
    reliable than the spectrum ranking (27% accurate).  We add a fixed prior
    bonus so fault_line ranks #1 when spectrum is inconclusive, but a
    discriminative constraint at a different line (Ochiai=1.0 with full weight)
    can still override it.

    prior_weight: added to fault_line's existing score.  Set to slightly above
    the maximum possible fine-grained constraint weight (1.0) so fault_line
    wins ties but a clearly-firing constraint at another line still wins.
    """
    if fault_line is None:
        return line_scores
    result = dict(line_scores)
    current = result.get(fault_line, 0.0)
    result[fault_line] = current + prior_weight
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from instrumentation import parse_constraints

    parser = argparse.ArgumentParser(
        description="Spectrum-based fault localization from CBFL violation reports."
    )
    parser.add_argument("violations", help="Path to cbfl_violations.jsonl")
    parser.add_argument("constraints", help="Path to constraints JSON file for the target SUT")
    parser.add_argument("program", nargs="?", help="Path to the buggy source program (optional)")
    parser.add_argument(
        "--sut",
        default=None,
        help="SUT name to analyse (default: inferred from violations in the JSONL)",
    )
    args = parser.parse_args()

    all_records = load_violations(args.violations)
    records = deduplicate_records(all_records)
    removed = len(all_records) - len(records)
    if removed:
        print(f"(Removed {removed} duplicate test-run entries from the report)")

    by_sut = group_by_sut(records)
    if by_sut:
        print(f"SUTs found in report: {', '.join(sorted(by_sut))}")

    sut_name = args.sut
    if sut_name is None:
        if len(by_sut) == 1:
            sut_name = next(iter(by_sut))
        elif len(by_sut) > 1:
            # Infer from constraints file name (e.g. "constraints/split_escaped.json" → "split_escaped")
            import os
            stem = os.path.splitext(os.path.basename(args.constraints))[0]
            if stem in by_sut:
                sut_name = stem
            else:
                print(
                    f"Multiple SUTs found ({', '.join(sorted(by_sut))}). "
                    "Specify one with --sut."
                )
                import sys; sys.exit(1)

    sut_records = by_sut.get(sut_name, [])
    print(f"\nAnalysing SUT: {sut_name!r}  ({len(sut_records)} records after dedup)\n")

    with open(args.constraints) as f:
        _, constraints = parse_constraints(f.read())

    cids = [c.cid for c in constraints]
    vm = build_matrix(sut_records, cids, sut=sut_name)
    scores = score_constraints(vm)
    ranked = rank_constraints(scores)

    print(f"Tests: {len(vm.passing)} passing, {len(vm.failing)} failing\n")
    print("Constraint rankings (Ochiai):")
    for cid, score in ranked:
        s = scores[cid]
        print(f"  {cid}: ochiai={score:.3f}  ef={s['ef']} ep={s['ep']} nf={s['nf']}")

    if args.program:
        with open(args.program) as f:
            src = f.read()
        line_scores = attribute_to_statements(scores, constraints, src)
        print("\nLine rankings:")
        for ln, score in rank_lines(line_scores):
            src_line = src.splitlines()[ln - 1].rstrip() if ln <= len(src.splitlines()) else ""
            print(f"  line {ln:3d} (score={score:.3f}): {src_line}")
