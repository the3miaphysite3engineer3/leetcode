# Local Solution Verification System

Verify your LeetCode solutions locally without submitting to LeetCode.

## Quick Start

```bash
# Verify a Python solution
python verify.py 1

# Verify a JavaScript solution
python verify.py 1 --lang js

# Verify a C++ solution
python verify.py 1 --lang cpp

# Verify all available languages at once
python verify.py 1 --all

# List all available test cases
python verify.py --list
```

## Requirements

- **Python 3.7+** – required for the verify script and Python solution runner
- **Node.js** – required for JavaScript and TypeScript solutions
- **g++ (C++17)** – required for C++ solutions

## Supported Languages

| Language   | Alias | Runner          | Requirement |
|------------|-------|-----------------|-------------|
| Python     | `py`  | Built-in        | Python 3.7+ |
| JavaScript | `js`  | Node.js         | Node.js     |
| TypeScript | `ts`  | Node.js (types stripped) | Node.js |
| C++        | `c++` | Compile & run   | g++ with C++17 |

## Usage

```
python verify.py <problem_number> [options]

positional arguments:
  problem               Problem number (e.g. 1 or 0001)

options:
  --lang LANG, -l LANG  Language to verify (default: python)
  --all, -a             Verify solution in all supported languages
  --verbose, -v         Show detailed test information
  --list                List available test cases
```

### Examples

```bash
# Basic usage - verifies the Python solution
python verify.py 1

# Use problem number with or without zero-padding
python verify.py 0001
python verify.py 1

# Specify language with full name or alias
python verify.py 70 --lang javascript
python verify.py 70 -l js

# Verbose mode shows inputs/outputs for all tests
python verify.py 121 -v

# Verify all languages at once
python verify.py 217 --all
```

## Adding Test Cases

Test cases are stored as JSON files in `tests/test_cases/`. Each file is named
by the zero-padded problem number (e.g., `0001.json`).

### Test Case Format

```json
{
    "problem_id": "0001",
    "title": "Two Sum",
    "function_name": "twoSum",
    "comparison": "sorted",
    "test_cases": [
        {
            "inputs": [[2, 7, 11, 15], 9],
            "expected": [0, 1]
        },
        {
            "inputs": [[3, 2, 4], 6],
            "expected": [1, 2]
        }
    ]
}
```

### Fields

| Field           | Required | Description |
|-----------------|----------|-------------|
| `problem_id`    | Yes      | Zero-padded problem number |
| `title`         | Yes      | Problem title |
| `function_name` | Yes      | Name of the method/function to call |
| `comparison`    | No       | Comparison method (default: `"exact"`) |
| `test_cases`    | Yes      | Array of test case objects |

### Test Case Object

| Field      | Description |
|------------|-------------|
| `inputs`   | Array of arguments to pass to the function |
| `expected` | The expected return value |

### Comparison Methods

| Method            | Description |
|-------------------|-------------|
| `exact`           | Values must match exactly (default) |
| `sorted`          | Arrays are sorted before comparison (e.g., Two Sum) |
| `unordered_lists` | For `List[List[...]]` where inner list order doesn't matter |
| `close`           | Floating point comparison with tolerance of 1e-5 |

### Step-by-Step: Adding a New Problem

1. Create `tests/test_cases/<PROBLEM_ID>.json` (e.g., `tests/test_cases/0015.json`)
2. Add the problem metadata and test cases following the format above
3. Find test cases on the LeetCode problem page or create your own
4. Run `python verify.py <number>` to verify

Example for problem 15 (3Sum):

```json
{
    "problem_id": "0015",
    "title": "3Sum",
    "function_name": "threeSum",
    "comparison": "unordered_lists",
    "test_cases": [
        {
            "inputs": [[-1, 0, 1, 2, -1, -4]],
            "expected": [[-1, -1, 2], [-1, 0, 1]]
        },
        {
            "inputs": [[0, 1, 1]],
            "expected": []
        },
        {
            "inputs": [[0, 0, 0]],
            "expected": [[0, 0, 0]]
        }
    ]
}
```

## Architecture

```
verify.py                   # Main CLI entry point
tests/
├── test_cases/             # Test case JSON files (one per problem)
│   ├── 0001.json
│   ├── 0020.json
│   └── ...
└── runners/                # Language-specific execution runners
    ├── python_runner.py    # Loads Solution class and calls methods
    ├── js_runner.js        # Evals JS code and calls functions
    └── ts_runner.js        # Strips TS types and runs as JS
```

### How It Works

1. **Load test cases** from the corresponding JSON file
2. **Find the solution file** in the language-specific directory
3. **Execute the solution** using the language runner:
   - **Python**: Imports the file, instantiates `Solution`, calls the method
   - **JavaScript**: Evals the file and calls the last function definition
   - **TypeScript**: Strips type annotations, then runs as JavaScript
   - **C++**: Generates a test harness with `main()`, compiles with g++, runs the binary
4. **Compare the result** with the expected output using the specified comparison method
5. **Report** pass/fail for each test case

### Notes on JavaScript Solutions

JavaScript solution files in this repository often contain multiple implementations
of the same function (e.g., brute force, optimized). Since they use `var` to
redefine the same function name, the **last definition** in the file is the one
that gets tested. This is typically the most optimized solution.

### Notes on C++ Solutions

The C++ runner automatically:
- Adds common `#include` directives (`bits/stdc++.h`)
- Infers parameter types from test inputs
- Generates a `main()` function that calls `Solution::method()`
- Compiles with `-std=c++17 -O2`
- Handles common return types: `int`, `bool`, `string`, `vector<int>`, etc.
