"""
counterfactual.py — Patch generation, re-execution, and fault classification.

For each top-ranked violated constraint, asks an LLM to generate a minimal fix,
applies it to the source, reruns the tests, and classifies the result as:
  Primary         — all failing tests now pass (root cause found)
  Secondary       — some improvement but not full resolution
  Irrelevant      — no change in test outcomes
  OverApproximate — constraint fires on passing tests (factual, from violations JSONL)
  Error           — LLM patch generation failed

Redundant constraints (dominated by a higher-ranked result) are flagged via
prune_redundant() after the main loop.

Usage:
    from counterfactual import CounterfactualVerifier
    verifier = CounterfactualVerifier()
    results = verifier.run(ranked_constraints, fn_src, src_path, test_path,
                           violations_path="violations/foo.jsonl")
    results = CounterfactualVerifier.prune_redundant(results)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Set, Tuple

from instrumentation import Constraint


def _load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (no overwrite)."""
    env_path = Path(path)
    if not env_path.exists():
        # Try repo root relative to this file
        env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


_load_dotenv()

Status = Literal["Primary", "Secondary", "Irrelevant", "OverApproximate", "Error"]

PATCH_SYSTEM_PROMPT = (
    "You are a minimal bug-fix assistant. "
    "Given a constraint that is violated and the buggy statement, "
    "produce a one-line Python fix that would make the constraint hold. "
    "Output ONLY the replacement Python statement, preserving indentation context. "
    "No explanation. No markdown. No code fences."
)


@dataclass
class TestOutcomes:
    passed: List[str]
    failed: List[str]


@dataclass
class VerificationResult:
    constraint: Constraint
    patch: str
    status: Status
    original_failing: List[str]
    patched_failing: List[str]
    pruned: bool = False
    prune_reason: str = ""


def _chat_completion(model: str, system: str, user: str) -> str:
    """
    Dispatch to OpenAI, Gemini, or Anthropic Vertex depending on model name.
    Returns the assistant's text content.
    """
    if model.startswith("gemini"):
        from google import genai
        from google.genai import types as genai_types

        key = os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=user,
            config=genai_types.GenerateContentConfig(
                system_instruction=system,
                temperature=0,
            ),
        )
        return response.text.strip()
    elif model.startswith("claude"):
        from anthropic import AnthropicVertex

        project_id = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
        region = os.environ.get("ANTHROPIC_VERTEX_REGION", "us-east5")
        client = AnthropicVertex(project_id=project_id, region=region)
        resp = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0,
        )
        return resp.content[0].text.strip()
    else:
        from openai import OpenAI

        key = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content.strip()


class CounterfactualVerifier:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        # api_key kept for backward-compat but is now unused (keys come from env / .env)
        self.model = model

    def generate_patch(
        self,
        constraint: Constraint,
        buggy_statement: str,
        fn_src: str,
    ) -> Optional[str]:
        """Ask the LLM to produce a minimal fix for the buggy statement."""
        prompt = (
            f"Constraint that must hold:\n  {constraint.spec.get('expr', '')}\n\n"
            f"Intent: {constraint.intent}\n\n"
            f"Buggy statement to fix:\n  {buggy_statement.strip()}\n\n"
            f"Full function for context:\n{fn_src}\n\n"
            "Produce one replacement line (same indentation level, just the code):"
        )
        try:
            return _chat_completion(self.model, PATCH_SYSTEM_PROMPT, prompt)
        except Exception as e:
            print(f"[counterfactual] LLM patch generation failed: {e}")
            return None

    def apply_patch(self, src: str, stmt_line: int, patch_line: str) -> str:
        """Replace the line at stmt_line (1-indexed) with patch_line, preserving indentation."""
        lines = src.splitlines(keepends=True)
        if 1 <= stmt_line <= len(lines):
            orig = lines[stmt_line - 1]
            indent = orig[: len(orig) - len(orig.lstrip())]
            stripped = patch_line.strip()
            lines[stmt_line - 1] = indent + stripped + "\n"
        return "".join(lines)

    def rerun_tests(
        self,
        patched_src: str,
        original_src_path: str,
        test_path: str,
    ) -> TestOutcomes:
        """
        Write patched source to a temp dir, run pytest with PYTHONPATH pointing there,
        and parse pass/fail outcomes.
        """
        # Mirror the package directory structure so package-style imports find the patch.
        # e.g. original_src_path = .../SemLoc/example_pipeline/programs/foo.py
        # → tmpdir/example_pipeline/programs/foo.py; add tmpdir to PYTHONPATH front.
        repo_root = os.path.dirname(os.path.abspath(__file__))
        try:
            rel_path = os.path.relpath(os.path.abspath(original_src_path), repo_root)
            # If src is outside repo_root, relpath starts with '..' — mirror as
            # programs/<basename> so test's `from programs.X import X` resolves.
            if rel_path.startswith('..'):
                rel_path = os.path.join("programs", os.path.basename(original_src_path))
        except ValueError:
            rel_path = os.path.join("programs", os.path.basename(original_src_path))

        with tempfile.TemporaryDirectory() as tmpdir:
            patched_path = os.path.join(tmpdir, rel_path)
            pkg_dir = os.path.dirname(patched_path)
            os.makedirs(pkg_dir, exist_ok=True)
            with open(patched_path, "w", encoding="utf-8") as f:
                f.write(patched_src)

            # Create __init__.py in every package directory under tmpdir so that
            # Python treats them as regular packages (not namespace packages).
            # Without these, Python merges the namespace package across sys.path
            # entries and may import from the original (un-patched) location.
            cur = pkg_dir
            while cur != tmpdir:
                init = os.path.join(cur, "__init__.py")
                if not os.path.exists(init):
                    open(init, "w").close()
                cur = os.path.dirname(cur)

            # Mirror the test file into tmpdir so that any sys.path.insert(N, dirname×k)
            # expressions inside the test resolve relative to tmpdir rather than the
            # original repo root (which would shadow the patched module).
            # Also copy the SemLoc conftest.py so that pytest plugins (e.g. --inst flag
            # registration) are available even without a rootdir pointing at the repo.
            import shutil
            try:
                test_rel = os.path.relpath(os.path.abspath(test_path), repo_root)
                if test_rel.startswith('..'):
                    test_rel = os.path.join("testcases", os.path.basename(test_path))
                mirrored_test = os.path.join(tmpdir, test_rel)
                os.makedirs(os.path.dirname(mirrored_test), exist_ok=True)
                shutil.copy2(test_path, mirrored_test)
                # Write a minimal conftest shim in the test directory so that
                # `pytest.inst` is defined (tests use `if pytest.inst:` guards).
                conftest_shim = os.path.join(os.path.dirname(mirrored_test), "conftest.py")
                if not os.path.exists(conftest_shim):
                    with open(conftest_shim, "w") as _cf:
                        _cf.write("import pytest\npytest.inst = False\n")
                run_test_path = mirrored_test
            except Exception:
                run_test_path = test_path

            env = os.environ.copy()
            existing = env.get("PYTHONPATH", "")
            # Add both tmpdir (for package-style imports) and pkg_dir (for flat
            # imports like `from foo import foo` used by the test files).
            env["PYTHONPATH"] = pkg_dir + ":" + tmpdir + (":" + existing if existing else "")

            result = subprocess.run(
                ["pytest", "-v", "--tb=no", "--disable-warnings", run_test_path],
                capture_output=True,
                text=True,
                env=env,
            )
            output = result.stdout + result.stderr

        passed, failed = [], []
        for line in output.splitlines():
            m = re.search(r"::(\S+)\s+(PASSED|FAILED)", line)
            if m:
                name, status = m.group(1), m.group(2)
                (passed if status == "PASSED" else failed).append(name)

        return TestOutcomes(passed=passed, failed=failed)

    def classify(
        self,
        baseline: TestOutcomes,
        patched: TestOutcomes,
        t_minus: List[str],
    ) -> Literal["Primary", "Secondary", "Irrelevant"]:
        """
        Primary    — all originally-failing tests now pass
        Secondary  — some originally-failing tests now pass (but not all)
        Irrelevant — no improvement
        """
        t_minus_set = set(t_minus)
        orig_failing = set(baseline.failed) & t_minus_set
        still_failing = set(patched.failed) & t_minus_set

        if not orig_failing:
            return "Irrelevant"
        if not still_failing:
            return "Primary"
        if len(still_failing) < len(orig_failing):
            return "Secondary"
        return "Irrelevant"

    @staticmethod
    def check_over_approximate(
        violations_path: str,
        cids: Optional[List[str]] = None,
    ) -> Set[str]:
        """
        Load a violations JSONL and return cids that fire on at least one
        *passing* test.  This is purely factual: if a constraint is violated
        during a run that ultimately passes, it is over-approximate (it flags
        correct behaviour as invalid).

        violations_path: cbfl_violations.jsonl written by conftest.py
        cids: optional allowlist; if given, only check these ids
        """
        over_approx: Set[str] = set()
        if not os.path.exists(violations_path):
            return over_approx

        cid_filter = set(cids) if cids else None
        with open(violations_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("outcome") != "passed":
                    continue
                for violation in record.get("violations", []):
                    # violation is a dict: {"sut": str, "cid": str, "reason": str}
                    cid = violation.get("cid") if isinstance(violation, dict) else None
                    if cid and (cid_filter is None or cid in cid_filter):
                        over_approx.add(cid)

        return over_approx

    @staticmethod
    def prune_redundant(results: List[VerificationResult]) -> List[VerificationResult]:
        """
        Mark results as redundant when they are dominated by a higher-ranked result.

        Constraint B is dominated by A (ranked earlier) when:
            frozenset(B.patched_failing) ⊇ frozenset(A.patched_failing)

        i.e. A fixes at least as many failing tests as B — keeping B adds nothing.
        Only Primary/Secondary results act as dominators (Irrelevant/Error/
        OverApproximate constraints don't establish a useful baseline to compare
        against).
        """
        DOMINATOR_STATUSES = {"Primary", "Secondary"}
        dominators: List[Tuple[int, frozenset]] = []

        for i, r in enumerate(results):
            if r.pruned:
                continue
            fs = frozenset(r.patched_failing)
            for j, dom_fs in dominators:
                if dom_fs <= fs:  # dominator leaves ≤ tests failing → B is redundant
                    r.pruned = True
                    r.prune_reason = (
                        f"Redundant: dominated by {results[j].constraint.cid} "
                        f"({len(dom_fs)} vs {len(fs)} tests still failing)"
                    )
                    break
            if not r.pruned and r.status in DOMINATOR_STATUSES:
                dominators.append((i, fs))

        return results

    def run(
        self,
        ranked_constraints: List[Tuple[Constraint, float, int]],
        fn_src: str,
        src_path: str,
        test_path: str,
        violations_path: Optional[str] = None,
    ) -> List[VerificationResult]:
        """
        For each (constraint, ochiai_score, anchor_line) in ranked order:
          1. Skip if over-approximate (fires on passing tests, per violations JSONL)
          2. Generate a patch via LLM
          3. Apply the patch
          4. Rerun tests
          5. Classify outcome
          6. Stop early if Primary is found

        Calls prune_redundant() before returning.

        violations_path: optional path to cbfl_violations.jsonl; enables
                         over-approximation detection when provided.
        """
        baseline = self.rerun_tests(fn_src, src_path, test_path)
        t_minus = baseline.failed

        if not t_minus:
            print("[counterfactual] No failing tests in baseline; nothing to verify.")
            return []

        # Pre-compute over-approximate cids from violations data (no LLM involved)
        all_cids = [c.cid for c, _, _ in ranked_constraints]
        over_approx_cids: Set[str] = set()
        if violations_path:
            over_approx_cids = self.check_over_approximate(violations_path, all_cids)
            if over_approx_cids:
                print(
                    f"[counterfactual] Over-approximate (fire on passing tests): "
                    f"{sorted(over_approx_cids)}"
                )

        results: List[VerificationResult] = []

        for constraint, score, anchor_line in ranked_constraints:
            if score == 0.0:
                continue

            if constraint.cid in over_approx_cids:
                results.append(VerificationResult(
                    constraint=constraint,
                    patch="",
                    status="OverApproximate",
                    original_failing=t_minus,
                    patched_failing=list(t_minus),
                ))
                print(
                    f"[counterfactual] {constraint.cid} (score={score:.3f}): "
                    f"OverApproximate — fires on passing tests, skipping"
                )
                continue

            src_lines = fn_src.splitlines()
            buggy_stmt = (
                src_lines[anchor_line - 1]
                if 1 <= anchor_line <= len(src_lines)
                else ""
            )

            patch = self.generate_patch(constraint, buggy_stmt, fn_src)
            if patch is None:
                results.append(VerificationResult(
                    constraint=constraint,
                    patch="",
                    status="Error",
                    original_failing=t_minus,
                    patched_failing=list(t_minus),
                ))
                continue

            patched_src = self.apply_patch(fn_src, anchor_line, patch)
            patched_outcomes = self.rerun_tests(patched_src, src_path, test_path)
            status = self.classify(baseline, patched_outcomes, t_minus)

            result = VerificationResult(
                constraint=constraint,
                patch=patch,
                status=status,
                original_failing=t_minus,
                patched_failing=patched_outcomes.failed,
            )
            results.append(result)
            print(
                f"[counterfactual] {constraint.cid} (score={score:.3f}, line={anchor_line}): "
                f"{status} — patch: {patch.strip()!r}"
            )

            if status == "Primary":
                break

        return self.prune_redundant(results)
