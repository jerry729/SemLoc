from openai import OpenAI
import os
import re
import subprocess
import ast
import json
import sys
from pathlib import Path
from prompt_template import build_llm_prompt

# Absolute path to the .env file next to this script
_ENV_FILE = Path(__file__).resolve().parent / ".env"

def _load_env() -> None:
    """Load .env using an absolute path with override=True."""
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE, override=True)
    except ImportError:
        pass


_load_env()


# ---------------------------------------------------
# Run test. Pytest result parsing and formatting
# ---------------------------------------------------


def extract_function_definitions(source):
    """
    Extracts all function definitions from Python source using AST.
    Also extracts methods from top-level class definitions.
    """
    functions = []
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_code = "\n".join(lines[node.lineno - 1:node.end_lineno])
                functions.append({"name": node.name, "source": func_code})
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        func_code = "\n".join(lines[item.lineno - 1:item.end_lineno])
                        functions.append({"name": item.name, "source": func_code})
    except Exception as e:
        print(f"Failed to parse source: {e}")
    return functions


def extract_program_file(source):
    return [source]


def load_json_testcases(json_dir, test_path):
    with open(test_path, "r") as f:
        code = f.read()
    if "load_testdata" not in code:
        return None
    m = re.search(r"load_json_testcases\((\w+)\.__name__\)", code)
    if not m:
        return None

    func_name = m.group(1)
    json_path = os.path.join(json_dir, f"{func_name}.json")

    if not os.path.exists(json_path):
        print(f"JSON test file not found: {json_path}")
        return None

    test_cases = []
    with open(json_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                pair = json.loads(line)
                if isinstance(pair, list) and len(pair) == 2:
                    input_data, expected_output = pair
                    test_cases.append((input_data, expected_output))
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON line: {line} with error {e}")
                continue
    return test_cases


def process_test_file(test_dir, test_file, json_dir, src_dir):

    # print(f"test_dir: {test_dir}")
    test_path = os.path.join(test_dir, test_file)
    print(f"\n▶ Running pytest on {test_path} ...")

    # Use verbose output for test results + traceback for errors
    cmd = ["pytest", "-v", "--tb=short", "--disable-warnings", test_path]
    process = subprocess.run(cmd, capture_output=True, text=True)
    output = process.stdout + process.stderr
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)  # Remove ANSI color codes

    print(f"▶ Extracting test runing result and test cases ...")
    passing, failing = [], []
    current_fail = None

    test_cases = load_json_testcases(json_dir, test_path)

    with open(test_path, "r") as f:
        test_code = f.read()
    test_functions = extract_function_definitions(test_code)

    parameterized_or_definition = "parameterized_test_data_or_function_definition"

    # Capture PASS/FAIL lines
    for line in output.splitlines():
        # Example lines:
        # tests/test_compute_average.py::test_non_empty_list PASSED
        # tests/test_compute_average.py::test_empty_list FAILED
        # print(f"{line}")
        m = re.search(r"(.+\.py)::([^\s]+)\s+(PASSED|FAILED).*", line.strip())
        if m:
            # print(f"Matched")
            file_name, test_name, status = m.groups()
            # print(f"file_name: {file_name}, test_name: {test_name}, status: {status}")
            if test_cases:
                data_or_function_id = int(
                    re.search(r"\[input_data(\d+).+\]", test_name).group(1)
                )
                data_or_function = test_cases[data_or_function_id]
                parameterized_or_definition = "parameterized_test_data"
            else:
                # Handle class-based tests: "TestClass::test_method" → "test_method"
                lookup_name = test_name.split("::")[-1] if "::" in test_name else test_name
                matched = [x for x in test_functions if x["name"] == lookup_name]
                if not matched:
                    # Skip unrecognized test names gracefully
                    continue
                data_or_function = matched[0]
                parameterized_or_definition = "test_function_definition"

            if status == "PASSED":
                passing.append(
                    {
                        "test_name": test_name,
                        parameterized_or_definition: data_or_function,
                        "status": "pass",
                    }
                )
            else:
                failing.append(
                    {
                        "test_name": test_name,
                        parameterized_or_definition: data_or_function,
                        "status": "fail",
                        "error": None,
                    }
                )

    # Extract error messages from summary at end of pytest output
    # Example:
    # E   ZeroDivisionError: division by zero
    error_lines = re.findall(r"E\s+([A-Za-z0-9_.]+Error:.*)", output)
    if error_lines and failing:
        # Attach errors to failing tests in order of occurrence
        for test, err in zip(failing, error_lines):
            test["error"] = err.strip()
            # print(f"✗ Test {test['test_name']} failed with error: {test['error']}")

    # Find corresponding source file (e.g., test_compute_average → compute_average.py)
    func_name = test_file.replace("test_", "").replace(".py", "")
    # print(f"src_dir: {src_dir}")
    # print(f"func_name: {func_name}")
    src_file = os.path.join(src_dir, f"{func_name}.py")
    # print(f"src_file: {src_file}")
    print(f"▶ Extracting function definitions from {src_file} ...")

    func_defs = []
    # print(f"Finding source file: {src_file}")
    if os.path.exists(src_file):
        # print(f"Found source file: {src_file}")
        with open(src_file) as f:
            src_code = f.read()
        func_defs = extract_program_file(src_code)
    return func_name, passing, failing, func_defs


def run_pytest(test_dir, test_file, json_dir, src_dir):
    """
    Run pytest per test file in verbose mode (-v).
    Extract passing and failing test functions and failure messages.
    Also extracts the target function definition from the source file.
    """
    all_results = []

    files_to_test = (
        [test_file]
        if test_file
        else [
            f
            for f in os.listdir(test_dir)
            if f.startswith("test_") and f.endswith(".py")
        ]
    )

    for test_file in files_to_test:

        if not test_file.startswith("test_") or not test_file.endswith(".py"):
            continue

        func_name, passing, failing, func_defs = process_test_file(
            test_dir, test_file, json_dir, src_dir
        )

        all_results.append(
            {
                "test_file": test_file,
                "target_function": func_name,
                "passing_tests": passing,
                "failing_tests": failing,
                "src_program": func_defs,
            }
        )

    return all_results


def _build_ssa_for(src_program: list, fn_name: str):
    """Try to build SSA form for the target function. Returns (ssa_code, def_map) or (None, None)."""
    try:
        from ssa import ExecutableSSA
        src = src_program[0] if src_program else ""
        result = ExecutableSSA().transform_function(src, fn_name)
        return result.source, result.def_map
    except Exception:
        return None, None


def _extract_fn_with_linenos(src_text: str, fn_name: str) -> str:
    """Return the target function source with 1-indexed file line numbers prefixed."""
    try:
        tree = ast.parse(src_text)
    except SyntaxError:
        return src_text
    src_lines = src_text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            fn_lines = src_lines[node.lineno - 1 : node.end_lineno]
            return "\n".join(
                f"{node.lineno + i:4d}: {line}" for i, line in enumerate(fn_lines)
            )
    return src_text


def build_prompt_for_all_python(save_dir, py_test_result_dir):
    folder = Path(py_test_result_dir)
    for file in folder.iterdir():
        if not file.suffix == ".json":
            continue
        with open(file, "r") as f:
            t = json.load(f)
        fn_name = t["target_function"]
        src_text = t["src_program"][0] if isinstance(t.get("src_program"), list) else t.get("src_program", "")
        program_code = _extract_fn_with_linenos(src_text, fn_name)
        ssa_code, def_map = _build_ssa_for(t["src_program"], fn_name)
        p = build_llm_prompt(
            program_code,
            t["passing_tests"],
            t["failing_tests"],
            ssa_code=ssa_code,
            def_map=def_map,
        )
        save_path = os.path.join(save_dir, f"{fn_name}.txt")
        with open(save_path, "w") as sf:
            sf.write(p)


def _strip_json_fences(text: str) -> str:
    """Extract valid JSON from an LLM response, handling prose and fences."""
    text = text.strip()
    # 1. Try a JSON code fence anywhere in the text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    # 2. Find the first { and walk to its matching closing brace
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1].strip()
    # 3. Fall back: strip leading/trailing fences only
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


_SYSTEM_PROMPT = (
    "You are a fault-localization assistant. "
    "You MUST output ONLY valid JSON — no prose, no explanation, no markdown fences. "
    "The JSON must exactly match the cbfl-ir-0.1 schema requested by the user."
)


def _query_openai(prompt: str, model: str, temperature: float = 0.0) -> str:
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
        raise ImportError(
            "google-genai is not installed. Run: pip install google-genai"
        )
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            f"GEMINI_API_KEY not set. Add it to {_ENV_FILE}"
        )
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
    """Query Claude via Anthropic Vertex AI (GCP).

    Requires:
      - pip install anthropic[vertex]
      - ANTHROPIC_VERTEX_PROJECT_ID env var (GCP project)
      - ANTHROPIC_VERTEX_REGION env var (default: us-east5)
    """
    try:
        from anthropic import AnthropicVertex
    except ImportError:
        raise ImportError(
            "anthropic[vertex] is not installed. Run: pip install 'anthropic[vertex]'"
        )
    _load_env()
    project_id = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
    region = os.environ.get("ANTHROPIC_VERTEX_REGION", "us-east5")
    if not project_id:
        raise EnvironmentError(
            "ANTHROPIC_VERTEX_PROJECT_ID not set. Add it to .env"
        )
    client = AnthropicVertex(project_id=project_id, region=region)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def query_llm_for_constraints(test_results, model: str = "gpt-4o",
                               temperature: float = 0.0):
    fn_name = test_results.get("target_function", "")
    src_list = test_results.get("src_program", [])
    src_text = src_list[0] if isinstance(src_list, list) and src_list else (src_list or "")
    program_code = _extract_fn_with_linenos(src_text, fn_name)
    ssa_code, def_map = _build_ssa_for(src_list, fn_name)

    prompt = build_llm_prompt(
        program_code,
        test_results["passing_tests"],
        test_results["failing_tests"],
        ssa_code=ssa_code,
        def_map=def_map,
    )

    if model.startswith("gemini"):
        raw = _query_gemini(prompt, model, temperature=temperature)
    elif model.startswith("claude"):
        raw = _query_claude_vertex(prompt, model, temperature=temperature)
    else:
        raw = _query_openai(prompt, model, temperature=temperature)

    content = _strip_json_fences(raw)
    try:
        return json.loads(content)
    except Exception:
        print(content)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SemLoc constraint inference — run individual pipeline steps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
steps:
  test    Run pytest on buggy programs; write execution/*.json
  prompt  Build LLM prompts from execution/*.json; write prompts/*.txt
  infer   Query LLM for constraints; write constraints/*.json
  all     Run test → prompt → infer  (default)

examples:
  python constraint_inference.py
  python constraint_inference.py --step infer --model gemini-2.0-flash
  python constraint_inference.py --step infer --func split_escaped --model gemini-2.0-flash
  python constraint_inference.py --step test --working-dir my_batch
        """,
    )
    parser.add_argument(
        "--working-dir", default="./example_batch", metavar="DIR",
        help="batch directory (default: ./example_batch)",
    )
    parser.add_argument(
        "--step", choices=["test", "prompt", "infer", "all"], default="all",
        help="which step to run (default: all)",
    )
    parser.add_argument(
        "--model", default="gemini-2.5-pro",
        help="LLM model for the infer step (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--func", default=None, metavar="NAME",
        help="restrict infer step to a single function name (e.g. split_escaped)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite existing output files",
    )
    args = parser.parse_args()

    wd = args.working_dir
    exec_dir   = os.path.join(wd, "execution")
    prompts_dir = os.path.join(wd, "prompts")
    constraints_dir = os.path.join(wd, "constraints")

    run_test   = args.step in ("test",   "all")
    run_prompt = args.step in ("prompt", "all")
    run_infer  = args.step in ("infer",  "all")

    # ── step: test ──────────────────────────────────────────────────────────
    if run_test:
        print("=== Running tests ===")
        os.makedirs(exec_dir, exist_ok=True)
        results = run_pytest(
            test_dir=os.path.join(wd, "testcases"),
            test_file=None,
            json_dir=os.path.join(wd, "json_testcases"),
            src_dir=os.path.join(wd, "programs"),
        )
        for tr in results:
            func_name = tr["target_function"]
            save_path = os.path.join(exec_dir, f"{func_name}.json")
            if not args.force and os.path.exists(save_path):
                print(f"  skip {func_name} (exists)")
                continue
            with open(save_path, "w") as f:
                json.dump(tr, f, indent=2)
            print(f"  saved {save_path}")

    # ── step: prompt ─────────────────────────────────────────────────────────
    if run_prompt:
        print("=== Building prompts ===")
        os.makedirs(prompts_dir, exist_ok=True)
        build_prompt_for_all_python(prompts_dir, exec_dir)
        print(f"  prompts written to {prompts_dir}/")

    # ── step: infer ──────────────────────────────────────────────────────────
    if run_infer:
        print(f"=== Querying LLM ({args.model}) ===")
        os.makedirs(constraints_dir, exist_ok=True)
        for json_file in sorted(Path(exec_dir).glob("*.json")):
            func_name = json_file.stem
            if args.func and func_name != args.func:
                continue
            out_path = os.path.join(constraints_dir, f"{func_name}.json")
            if not args.force and os.path.exists(out_path):
                print(f"  skip {func_name} (exists)")
                continue
            with open(json_file) as f:
                test_results = json.load(f)
            print(f"  querying for {func_name}…")
            try:
                constraints = query_llm_for_constraints(test_results, model=args.model)
                with open(out_path, "w") as f:
                    json.dump(constraints, f, indent=2)
                print(f"  saved {out_path}")
            except Exception as e:
                print(f"  ERROR for {func_name}: {e}")
