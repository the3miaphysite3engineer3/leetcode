#!/usr/bin/env python3
"""Runner for Python LeetCode solutions.

Usage: python python_runner.py <solution_file> <function_name> <inputs_json>

Loads the solution file, creates a Solution instance, calls the specified
method with the given inputs, and prints the result as JSON.
"""
import sys
import json
import math
import heapq
import bisect
import collections
import itertools
import functools
from typing import List, Optional, Dict, Set, Tuple, Any


def main():
    if len(sys.argv) != 4:
        print("Usage: python python_runner.py <solution_file> <function_name> <inputs_json>",
              file=sys.stderr)
        sys.exit(1)

    solution_file = sys.argv[1]
    function_name = sys.argv[2]
    inputs = json.loads(sys.argv[3])

    # Read solution code
    with open(solution_file) as f:
        code = f.read()

    # Create execution environment with common LeetCode imports
    env = {
        "__builtins__": __builtins__,
        "List": List,
        "Optional": Optional,
        "Dict": Dict,
        "Set": Set,
        "Tuple": Tuple,
        "Any": Any,
        "math": math,
        "heapq": heapq,
        "bisect": bisect,
        "collections": collections,
        "itertools": itertools,
        "functools": functools,
        "defaultdict": collections.defaultdict,
        "Counter": collections.Counter,
        "deque": collections.deque,
        "inf": float("inf"),
    }

    # Execute solution code
    exec(code, env)

    # Find and instantiate the Solution class
    if "Solution" not in env:
        print("Error: No 'Solution' class found in the file", file=sys.stderr)
        sys.exit(1)

    sol = env["Solution"]()
    method = getattr(sol, function_name, None)
    if method is None:
        print(f"Error: Method '{function_name}' not found in Solution class",
              file=sys.stderr)
        sys.exit(1)

    # Call the method with inputs
    result = method(*inputs)

    # Output result as JSON
    print(json.dumps(result))


if __name__ == "__main__":
    main()
