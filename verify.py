#!/usr/bin/env python3
"""
Local Solution Verification System for LeetCode Problems
=========================================================

Verifies LeetCode solutions against test cases locally without needing
to submit to LeetCode.

Usage:
    python verify.py <problem_number> [--lang <language>] [--all] [--verbose]
    python verify.py --list

Examples:
    python verify.py 1                    # Verify Python solution for problem 1
    python verify.py 0001 --lang js       # Verify JavaScript solution
    python verify.py 1 --all              # Verify all available language solutions
    python verify.py --list               # List available test cases
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()
TEST_CASES_DIR = REPO_ROOT / "tests" / "test_cases"
RUNNERS_DIR = REPO_ROOT / "tests" / "runners"

# Mapping from language name to directory name in the repository
LANG_DIRS = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "cpp": "cpp",
    "java": "java",
    "go": "go",
    "c": "c",
    "csharp": "csharp",
    "kotlin": "kotlin",
    "rust": "rust",
    "ruby": "ruby",
    "swift": "swift",
    "scala": "scala",
    "dart": "dart",
}

# Mapping from language name to file extension
LANG_EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "cpp": ".cpp",
    "java": ".java",
    "go": ".go",
    "c": ".c",
    "csharp": ".cs",
    "kotlin": ".kt",
    "rust": ".rs",
    "ruby": ".rb",
    "swift": ".swift",
    "scala": ".scala",
    "dart": ".dart",
}

# Language aliases for convenience
LANG_ALIASES = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "c++": "cpp",
    "cs": "csharp",
    "kt": "kotlin",
    "rs": "rust",
    "rb": "ruby",
}

TIMEOUT_SECONDS = 10
CPP_COMPILE_TIMEOUT = 30


# ──────────────────────────────────────────────────────────────────────
# Terminal colors
# ──────────────────────────────────────────────────────────────────────
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def _no_color():
    """Disable colors when output is not a terminal."""
    Colors.GREEN = ""
    Colors.RED = ""
    Colors.YELLOW = ""
    Colors.BLUE = ""
    Colors.BOLD = ""
    Colors.END = ""


# ──────────────────────────────────────────────────────────────────────
# Test case and solution file helpers
# ──────────────────────────────────────────────────────────────────────
def load_test_cases(problem_id):
    """Load test cases for a given problem.

    Returns (data_dict, file_path) or (None, file_path) if not found.
    """
    padded = str(problem_id).zfill(4)
    path = TEST_CASES_DIR / f"{padded}.json"
    if not path.exists():
        return None, path
    with open(path) as f:
        return json.load(f), path


def find_solution_file(problem_id, language):
    """Find the solution file for a given problem and language."""
    padded = str(problem_id).zfill(4)
    lang_dir = REPO_ROOT / LANG_DIRS.get(language, language)
    ext = LANG_EXTENSIONS.get(language)
    if not lang_dir.exists() or ext is None:
        return None
    for f in sorted(lang_dir.iterdir()):
        if f.name.startswith(padded + "-") and f.suffix == ext:
            return f
    return None


def resolve_language(name):
    """Resolve a language alias to its canonical name."""
    return LANG_ALIASES.get(name.lower(), name.lower())


# ──────────────────────────────────────────────────────────────────────
# Result comparison
# ──────────────────────────────────────────────────────────────────────
def compare_results(actual, expected, comparison="exact"):
    """Compare actual vs expected using the specified comparison method."""
    if comparison == "exact":
        return actual == expected
    if comparison == "sorted":
        if isinstance(actual, list) and isinstance(expected, list):
            return sorted(actual) == sorted(expected)
        return actual == expected
    if comparison == "unordered_lists":
        # For List[List[...]] where inner list order doesn't matter
        if isinstance(actual, list) and isinstance(expected, list):
            if len(actual) != len(expected):
                return False

            def _normalize_nested(lst):
                return sorted(sorted(x) if isinstance(x, list) else [x] for x in lst)

            return _normalize_nested(actual) == _normalize_nested(expected)
        return actual == expected
    if comparison == "close":
        try:
            return abs(float(actual) - float(expected)) < 1e-5
        except (TypeError, ValueError):
            return actual == expected
    return actual == expected


# ──────────────────────────────────────────────────────────────────────
# Language runners
# ──────────────────────────────────────────────────────────────────────
def _run_subprocess(cmd, timeout=TIMEOUT_SECONDS):
    """Run a command and return (parsed_json_output, error_string)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
        )
        if proc.returncode != 0:
            return None, proc.stderr.strip()
        return json.loads(proc.stdout.strip()), None
    except subprocess.TimeoutExpired:
        return None, f"Time Limit Exceeded (timeout: {timeout}s)"
    except json.JSONDecodeError:
        return None, f"Failed to parse output: {proc.stdout.strip()}"
    except FileNotFoundError as exc:
        return None, f"Command not found: {exc.filename}"
    except Exception as exc:
        return None, str(exc)


def run_python(solution_file, function_name, inputs, mode="default", **_kwargs):
    """Run a Python solution."""
    runner = RUNNERS_DIR / "python_runner.py"
    cmd = [sys.executable, str(runner), str(solution_file), function_name, json.dumps(inputs)]
    if mode != "default":
        cmd.append(mode)
    return _run_subprocess(cmd)


def run_javascript(solution_file, function_name, inputs, **_kwargs):
    """Run a JavaScript solution."""
    runner = RUNNERS_DIR / "js_runner.js"
    return _run_subprocess(
        ["node", str(runner), str(solution_file), function_name, json.dumps(inputs)]
    )


def run_typescript(solution_file, function_name, inputs, **_kwargs):
    """Run a TypeScript solution (strips types then runs as JS)."""
    runner = RUNNERS_DIR / "ts_runner.js"
    return _run_subprocess(
        ["node", str(runner), str(solution_file), function_name, json.dumps(inputs)]
    )


# ──────────────── C++ helpers ────────────────────────────────────────
def _infer_cpp_type(value):
    """Infer a C++ type from a JSON value."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return "vector<int>"
        inner = _infer_cpp_type(value[0])
        return f"vector<{inner}>"
    return "auto"


def _to_cpp_literal(value):
    """Convert a JSON value to a C++ literal string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        inner = ", ".join(_to_cpp_literal(v) for v in value)
        return "{" + inner + "}"
    return str(value)


_CPP_PRINT_FUNCS = r"""
// ---------- generic result printers ----------
void _printResult(int v)            { cout << v << "\n"; }
void _printResult(long long v)      { cout << v << "\n"; }
void _printResult(bool v)           { cout << (v ? "true" : "false") << "\n"; }
void _printResult(double v)         { cout << fixed << setprecision(5) << v << "\n"; }
void _printResult(const string& v)  { cout << "\"" << v << "\"\n"; }
void _printResult(const vector<int>& v) {
    cout << "[";
    for (size_t i = 0; i < v.size(); i++) { if (i) cout << ","; cout << v[i]; }
    cout << "]\n";
}
void _printResult(const vector<string>& v) {
    cout << "[";
    for (size_t i = 0; i < v.size(); i++) { if (i) cout << ","; cout << "\"" << v[i] << "\""; }
    cout << "]\n";
}
void _printResult(const vector<vector<int>>& v) {
    cout << "[";
    for (size_t i = 0; i < v.size(); i++) {
        if (i) cout << ",";
        cout << "[";
        for (size_t j = 0; j < v[i].size(); j++) { if (j) cout << ","; cout << v[i][j]; }
        cout << "]";
    }
    cout << "]\n";
}
"""


def run_cpp(solution_file, function_name, inputs, expected=None, **_kwargs):
    """Run a C++ solution by generating a harness, compiling, and executing."""
    with open(solution_file) as f:
        solution_code = f.read()

    # Build parameter declarations
    decls, names = [], []
    for i, val in enumerate(inputs):
        ctype = _infer_cpp_type(val)
        lit = _to_cpp_literal(val)
        decls.append(f"    {ctype} p{i} = {lit};")
        names.append(f"p{i}")

    harness = (
        "#include <bits/stdc++.h>\nusing namespace std;\n\n"
        + solution_code
        + "\n"
        + _CPP_PRINT_FUNCS
        + "\nint main() {\n"
        + "    Solution sol;\n"
        + "\n".join(decls)
        + "\n"
        + f"    auto result = sol.{function_name}({', '.join(names)});\n"
        + "    _printResult(result);\n"
        + "    return 0;\n}\n"
    )

    src_fd, src_path = tempfile.mkstemp(suffix=".cpp")
    exe_path = src_path.replace(".cpp", "")
    try:
        with os.fdopen(src_fd, "w") as f:
            f.write(harness)

        # Compile
        comp = subprocess.run(
            ["g++", "-std=c++17", "-O2", "-o", exe_path, src_path],
            capture_output=True,
            text=True,
            timeout=CPP_COMPILE_TIMEOUT,
        )
        if comp.returncode != 0:
            return None, f"Compilation error:\n{comp.stderr.strip()}"

        # Run
        proc = subprocess.run(
            [exe_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        if proc.returncode != 0:
            return None, f"Runtime error:\n{proc.stderr.strip()}"

        return json.loads(proc.stdout.strip()), None
    except subprocess.TimeoutExpired:
        return None, f"Time Limit Exceeded"
    except json.JSONDecodeError:
        return None, f"Failed to parse output: {proc.stdout.strip()}"
    except FileNotFoundError:
        return None, "g++ not found. Install g++ to verify C++ solutions."
    except Exception as exc:
        return None, str(exc)
    finally:
        for p in (src_path, exe_path):
            try:
                os.unlink(p)
            except OSError:
                pass


# Supported language runners
RUNNERS = {
    "python": run_python,
    "javascript": run_javascript,
    "typescript": run_typescript,
    "cpp": run_cpp,
}


def run_solution(language, solution_file, function_name, inputs, expected=None, mode="default"):
    """Dispatch to the appropriate language runner."""
    runner = RUNNERS.get(language)
    if runner is None:
        return None, f"No runner available for '{language}'. Supported: {', '.join(sorted(RUNNERS))}"
    return runner(solution_file, function_name, inputs, expected=expected, mode=mode)


# ──────────────────────────────────────────────────────────────────────
# Verification logic
# ──────────────────────────────────────────────────────────────────────
def verify_problem(problem_id, language, verbose=False):
    """Verify a solution for a given problem and language.

    Returns True (all passed), False (some failed), or None (skipped).
    """
    test_data, test_path = load_test_cases(problem_id)
    if test_data is None:
        print(f"{Colors.RED}✗ No test cases found for problem {str(problem_id).zfill(4)}{Colors.END}")
        print(f"  Expected: {test_path}")
        return False

    solution_file = find_solution_file(problem_id, language)
    if solution_file is None:
        print(f"{Colors.YELLOW}⊘ No {language} solution found for problem "
              f"{str(problem_id).zfill(4)}{Colors.END}")
        return None

    fn_name = test_data["function_name"]
    comparison = test_data.get("comparison", "exact")
    mode = test_data.get("mode", "default")
    cases = test_data["test_cases"]
    title = test_data.get("title", "")

    print(f"\n{Colors.BOLD}{Colors.BLUE}Problem {str(problem_id).zfill(4)}: "
          f"{title}{Colors.END}")
    print(f"  Language:  {language}")
    print(f"  File:      {solution_file.relative_to(REPO_ROOT)}")
    print(f"  Function:  {fn_name}")
    print(f"  Tests:     {len(cases)}")
    print()

    passed = failed = 0

    for i, tc in enumerate(cases, 1):
        inputs = tc["inputs"]
        expected = tc["expected"]

        result, error = run_solution(language, solution_file, fn_name, inputs, expected, mode=mode)

        if error:
            print(f"  {Colors.RED}✗ Test {i}: ERROR{Colors.END}")
            if verbose:
                print(f"    Input:    {json.dumps(inputs)}")
                print(f"    Expected: {json.dumps(expected)}")
            print(f"    Error:    {error}")
            failed += 1
        elif compare_results(result, expected, comparison):
            print(f"  {Colors.GREEN}✓ Test {i}: PASSED{Colors.END}")
            if verbose:
                print(f"    Input:    {json.dumps(inputs)}")
                print(f"    Expected: {json.dumps(expected)}")
                print(f"    Got:      {json.dumps(result)}")
            passed += 1
        else:
            print(f"  {Colors.RED}✗ Test {i}: FAILED{Colors.END}")
            print(f"    Input:    {json.dumps(inputs)}")
            print(f"    Expected: {json.dumps(expected)}")
            print(f"    Got:      {json.dumps(result)}")
            failed += 1

    print()
    if failed == 0:
        print(f"  {Colors.GREEN}{Colors.BOLD}All {passed} tests passed! ✓{Colors.END}")
        return True
    else:
        print(f"  {Colors.RED}{Colors.BOLD}{failed}/{passed + failed} tests failed ✗{Colors.END}")
        return False


def list_test_cases():
    """Print a list of all available test cases."""
    if not TEST_CASES_DIR.exists():
        print("No test cases directory found.")
        return

    files = sorted(TEST_CASES_DIR.glob("*.json"))
    if not files:
        print("No test cases found.")
        return

    print(f"\n{Colors.BOLD}Available Test Cases:{Colors.END}\n")
    for tf in files:
        with open(tf) as f:
            data = json.load(f)
        pid = data.get("problem_id", tf.stem)
        title = data.get("title", "")
        num = len(data.get("test_cases", []))

        # Determine which languages have solutions
        langs = [lang for lang in RUNNERS if find_solution_file(int(pid), lang)]

        print(f"  {Colors.BLUE}{pid}{Colors.END} - {title} ({num} test cases)")
        print(f"         Solutions: {', '.join(langs) if langs else 'none'}")
    print()


# ──────────────────────────────────────────────────────────────────────
# CLI entry-point
# ──────────────────────────────────────────────────────────────────────
def main():
    if not sys.stdout.isatty():
        _no_color()

    parser = argparse.ArgumentParser(
        description="Verify LeetCode solutions locally against test cases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verify.py 1                    Verify Python solution for problem 1
  python verify.py 0001 --lang js       Verify JavaScript solution
  python verify.py 1 --all              Verify all available language solutions
  python verify.py 1 -v                 Verbose output with all test details
  python verify.py --list               List available test cases""",
    )
    parser.add_argument(
        "problem", nargs="?",
        help="Problem number (e.g. 1 or 0001)",
    )
    parser.add_argument(
        "--lang", "-l", default="python",
        help="Language to verify (default: python). Aliases: py, js, ts, c++",
    )
    parser.add_argument(
        "--all", "-a", action="store_true",
        help="Verify solution in all supported languages",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed test information",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available test cases",
    )

    args = parser.parse_args()

    if args.list:
        list_test_cases()
        return

    if not args.problem:
        parser.print_help()
        sys.exit(1)

    try:
        problem_id = int(args.problem)
    except ValueError:
        print(f"Error: Invalid problem number: {args.problem}")
        sys.exit(1)

    if args.all:
        results = {}
        for lang in RUNNERS:
            result = verify_problem(problem_id, lang, args.verbose)
            if result is not None:
                results[lang] = result

        # Summary
        print(f"\n{'=' * 50}")
        print(f"{Colors.BOLD}Summary for Problem {str(problem_id).zfill(4)}:{Colors.END}")
        for lang, ok in results.items():
            icon = f"{Colors.GREEN}PASSED ✓{Colors.END}" if ok else f"{Colors.RED}FAILED ✗{Colors.END}"
            print(f"  {lang:15s} {icon}")

        sys.exit(0 if all(results.values()) else 1)
    else:
        language = resolve_language(args.lang)
        if language not in RUNNERS:
            print(f"Error: No runner for '{language}'. Supported: {', '.join(sorted(RUNNERS))}")
            sys.exit(1)

        result = verify_problem(problem_id, language, args.verbose)
        if result is None:
            sys.exit(1)
        sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
