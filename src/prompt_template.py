from string import Template
from typing import Dict, Optional, Tuple

prompt_tpl = Template(
    """You are a fault-localization expert.  Given a buggy Python function and \
passing/failing tests, your job is to:
  1. Identify the specific line or expression most likely to contain the bug.
  2. Place semantic constraints DIRECTLY AT that location so a spectrum-based \
tool can rank it as the most suspicious line.

━━━ Output format (STRICT) ━━━

Output only valid JSON — no prose, no markdown fences.

Schema:

{
  "version": "cbfl-ir-0.1",
  "function_name": "<string>",
  "fault_hypothesis": "<1–2 sentences: what is wrong and on which line/variable>",
  "fault_line": <int — the 1-indexed source line number most likely to be buggy>,
  "constraints": [
    {
      "id": "C1",
      "category": "<ONE_OF_ALLOWED_CATEGORIES>",
      "instrument": {
        "region": "<ONE_OF_ALLOWED_REGIONS>",
        "anchor": { }
      },
      "spec": {
        "expr": "<boolean expression — use SSA-versioned names when SSA Form is provided>"
      },
      "intent": "<1 short sentence>",
      "confidence": <float 0..1>
    }
  ]
}

━━━ Constraint placement strategy ━━━

MANDATORY: You MUST generate exactly one constraint using region LINE at the
fault_line you identified.  This constraint must check an expression that will
be FALSE on failing tests and TRUE on passing tests.  Without this constraint
the tool cannot rank the faulty line as most suspicious.

PRIMARY goal: pinpoint the faulty statement.
  • 1 constraint MUST use LINE with anchor {"line": <fault_line>}
      — check a condition that is violated right after the buggy statement
  • At least 2 more constraints MUST use fine-grained regions:
      AFTER_DEF    — check a value immediately after it is assigned
      BEFORE_USE   — check a value immediately before it is used
      AFTER_BRANCH — check at end of an if/else branch: {"if_line": N, "branch": "then"|"else"}
      LOOP_TAIL    — check invariants at the end of each loop iteration
  • Anchor AFTER_DEF / BEFORE_USE constraints to SSA variables near fault_line.

SUPPLEMENTARY (at most 2 constraints total):
  ANY_RETURN / EXIT — only to catch output-level symptoms; these cannot
                      pinpoint the fault and are scored with 0.3× weight.
  ENTRY             — only for precondition checks on inputs (0.2× weight).

Do NOT generate more than 2 ANY_RETURN/EXIT/ENTRY constraints combined.
If the bug is inside a loop, prefer LOOP_TAIL over ANY_RETURN.

━━━ Allowed category values ━━━
PRECONDITION  POSTCONDITION  VALUE_RANGE  RELATION  DERIVED_CONSISTENCY
INVARIANT_LOOP  TEMPORAL_CALL_SNAPSHOT  TEMPORAL_UNTIL_OVERWRITTEN
TEMPORAL_RESOURCE_LIFETIME

━━━ Allowed instrument.region values ━━━
FINE-GRAINED (prefer these, full 1.0× weight in scoring):
  LINE         — check after the statement at a specific line ← USE THIS AT fault_line
  AFTER_DEF   — check after definition/assignment of a variable
  BEFORE_USE  — check immediately before a variable is used
  AFTER_BRANCH — check at the end of an if/else branch body
  LOOP_TAIL   — check at end of each loop iteration
  LOOP_HEAD   — check at start of each loop iteration
  AFTER_CALL  — check after a call to some callee

COARSE (supplementary only):
  ANY_RETURN  — check before every return   ← scores with 0.3× weight
  EXIT        — check once at single exit   ← scores with 0.3× weight
  ENTRY       — check at function entry     ← scores with 0.2× weight
  ON_EXIT     — run even on exceptions (temporal)

━━━ instrument.anchor rules ━━━
LINE        → {"line": <int>}         e.g. {"line": 67}   (1-indexed source line)
AFTER_DEF  → {"var": "<ssa_name>"}   e.g. {"var": "x__2"}
BEFORE_USE → {"var": "<ssa_name>"}
AFTER_CALL → {"callee": "<name>"}
AFTER_BRANCH → {"if_line": <int>, "branch": "then"|"else"}
LOOP_HEAD / LOOP_TAIL → {"loop_id": <int>}   matches "# loop__id: N" in SSA Form
All others → {}

━━━ Expression language rules (spec.expr) ━━━
Python-like booleans: and, or, not, comparisons, arithmetic.
Builtins: len(x), abs(x), all(<genexpr>), any(<genexpr>), sum(<genexpr>).
Return value: __cbfl_result
SSA names: use versioned names (x__2) in AFTER_DEF/BEFORE_USE anchored constraints.
For ENTRY / ANY_RETURN / EXIT: use original parameter names (no SSA suffix).

━━━ Category-specific spec requirements ━━━

PRECONDITION / POSTCONDITION / VALUE_RANGE / RELATION /
DERIVED_CONSISTENCY / INVARIANT_LOOP:
  spec: {"expr": "<boolean expr>"}

TEMPORAL_CALL_SNAPSHOT — instrument.region must be ON_EXIT:
  spec: {
    "guard": "<bool at entry>",
    "snapshot": [{"name": "<id>", "expr": "<expr at entry>"}],
    "require": "<bool at exit referencing snapshot names>"
  }

TEMPORAL_UNTIL_OVERWRITTEN — only for read/write/delete APIs:
  spec: {"role": "WRITE"|"READ"|"KILL", "key_expr": "<expr>", "value_expr": "<expr>"}
  region: ANY_RETURN (READ) or EXIT/ANY_RETURN (WRITE/KILL)

TEMPORAL_RESOURCE_LIFETIME — only for acquire/release patterns:
  spec: {"acquire_call": "<callee>", "release_call": "<callee>", "handle_expr": "<expr>"}
  region: ON_EXIT

━━━ Quality checklist ━━━
✓ fault_line is the integer line number of the suspected buggy statement
✓ Exactly 1 constraint uses region=LINE with anchor={"line": fault_line}
✓ That LINE constraint expr is FALSE on failing tests, TRUE on passing tests
✓ At least 2 more constraints use AFTER_DEF / BEFORE_USE / AFTER_BRANCH / LOOP_TAIL
✓ All constraints are checkable at runtime with data available in the function
✗ Do NOT write trivially-true constraints (x == x, len(x) >= 0)
✗ Do NOT write more than 2 coarse (ENTRY/ANY_RETURN/EXIT) constraints

### Program (line numbers are 1-indexed file line numbers):
$code
$ssa_section
---

### Passing Tests:
$passing

---

### Failing Tests with Errors:
$failing


Return only the JSON.
"""
)


def _format_ssa_section(ssa_code: Optional[str], def_map: Optional[Dict[str, Tuple]]) -> str:
    """Format the SSA section for the prompt, or return empty string."""
    if not ssa_code:
        return ""
    lines = [
        "\n---",
        "\n### SSA Form",
        "# Variable naming: x__N is the N-th definition of variable x.",
        "# Use SSA names in anchor.var (AFTER_DEF/BEFORE_USE) and in spec.expr.",
        "# Loops are annotated with '# loop__id: N' — use that integer in anchor.loop_id",
        "# for LOOP_HEAD/LOOP_TAIL constraints.",
        "# Each statement is annotated with '# L<N>' — the 1-indexed original source line number.",
        "# Use these L<N> values for fault_line and for anchor.line in LINE constraints.",
    ]
    if def_map:
        lines.append("#")
        lines.append("# SSA variable  ->  original name  (defined at source byte)")
        for ssa_name, (base, byte_offset) in sorted(def_map.items()):
            lines.append(f"# {ssa_name:<20} -> '{base}'  (byte {byte_offset})")
    lines.append("")
    lines.append(ssa_code)
    return "\n".join(lines) + "\n"


def build_llm_prompt(program_code, passing, failing, ssa_code=None, def_map=None):
    ssa_section = _format_ssa_section(ssa_code, def_map)
    prompt = prompt_tpl.substitute(
        code=program_code,
        passing=passing,
        failing=failing,
        ssa_section=ssa_section,
    )
    return prompt


_REFINEMENT_TPL = Template(
    """You are a fault-localization expert refining a second round of constraints.

Round 1 is complete.  The evidence below shows which constraints fired and \
which lines were ranked suspicious.  Your task: generate ADDITIONAL fine-grained \
constraints that narrow the fault to the single most suspicious statement.

Output the same JSON schema (cbfl-ir-0.1) including a fault_hypothesis field. \
Do NOT repeat any constraint from round 1.

━━━ Placement rules (same as round 1) ━━━
• At least 3 new constraints must use AFTER_DEF, BEFORE_USE, or LOOP_TAIL.
• Anchor them to SSA variables defined near the top-ranked suspicious lines.
• At most 2 coarse constraints (ANY_RETURN / EXIT / ENTRY) in this batch.

### Program (line numbers are 1-indexed file line numbers):
$code
$ssa_section
---

### Passing Tests:
$passing

---

### Failing Tests with Errors:
$failing

---

### First-Round Constraint Evidence

**Discriminative constraints** (violated ONLY on failing tests — near the fault):
$discriminative

**Over-approximate constraints** (violated on both passing and failing — too broad):
$over_approx

**Silent constraints** (never violated — may be checking the wrong location):
$silent

**Top-ranked suspicious lines from first round** (line number: score):
$ranked_lines

---

Focus new constraints on the variables and statements implicated by the \
discriminative constraints and top-ranked lines above.
Use AFTER_DEF anchored to SSA variables assigned at those lines.

Return only the JSON.
"""
)


def build_refinement_prompt(
    program_code,
    passing,
    failing,
    discriminative: list,
    over_approx: list,
    silent: list,
    ranked_lines: list,
    ssa_code=None,
    def_map=None,
) -> str:
    """Build a second-round prompt that feeds back violation evidence."""
    ssa_section = _format_ssa_section(ssa_code, def_map)

    def _fmt_constraints(clist):
        if not clist:
            return "  (none)"
        lines = []
        for c in clist:
            expr = c.get("spec", {}).get("expr") or str(c.get("spec", ""))
            region = c.get("instrument", {}).get("region", c.get("region", "?"))
            anchor = c.get("instrument", {}).get("anchor", c.get("anchor", {}))
            intent = c.get("intent", "")
            lines.append(
                f"  [{c['id']}] region={region} anchor={anchor}  expr={expr!r}  intent={intent!r}"
            )
        return "\n".join(lines)

    ranked_str = "\n".join(
        f"  line {ln}: {score:.4f}" for ln, score in ranked_lines[:10]
    ) if ranked_lines else "  (no ranking available)"

    return _REFINEMENT_TPL.substitute(
        code=program_code,
        ssa_section=ssa_section,
        passing=passing,
        failing=failing,
        discriminative=_fmt_constraints(discriminative),
        over_approx=_fmt_constraints(over_approx),
        silent=_fmt_constraints(silent),
        ranked_lines=ranked_str,
    )
