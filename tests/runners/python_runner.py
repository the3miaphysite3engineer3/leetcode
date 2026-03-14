#!/usr/bin/env python3
"""Runner for Python LeetCode solutions.

Usage: python python_runner.py <solution_file> <function_name> <inputs_json>

Loads the solution file, creates a Solution instance, calls the specified
method with the given inputs, and prints the result as JSON.

Supports special input/output modes via an optional 4th argument:
  - "linked_list":  convert list<->ListNode for inputs/outputs
  - "tree":         convert list<->TreeNode for inputs/outputs
  - "inplace":      return mutated input instead of function return value
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


# ──────────────────────────────────────────────────────────────────────
# Data-structure helpers
# ──────────────────────────────────────────────────────────────────────
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def list_to_linked(arr):
    """Convert a Python list to a ListNode linked list."""
    if not arr:
        return None
    head = ListNode(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def linked_to_list(head):
    """Convert a ListNode linked list to a Python list."""
    result = []
    seen = set()
    while head and id(head) not in seen:
        seen.add(id(head))
        result.append(head.val)
        head = head.next
    return result


def list_to_tree(arr):
    """Convert a level-order list (with None gaps) to a TreeNode tree."""
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    queue = collections.deque([root])
    i = 1
    while queue and i < len(arr):
        node = queue.popleft()
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root


def tree_to_list(root):
    """Convert a TreeNode tree to a level-order list (with None gaps)."""
    if root is None:
        return []
    result = []
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    # Remove trailing Nones
    while result and result[-1] is None:
        result.pop()
    return result


def _build_env(code):
    """Create execution environment, exec code, and return the namespace."""
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
        "heapify": heapq.heapify,
        "heappush": heapq.heappush,
        "heappop": heapq.heappop,
        "heappushpop": heapq.heappushpop,
        "heapreplace": heapq.heapreplace,
        "cmp_to_key": functools.cmp_to_key,
        "lru_cache": functools.lru_cache,
        "cache": functools.cache,
        "reduce": functools.reduce,
        "random": __import__("random"),
        "math": __import__("math"),
        "ceil": math.ceil,
        "floor": math.floor,
        "sqrt": math.sqrt,
        "log": math.log,
        "log2": math.log2,
        "gcd": math.gcd,
        "ListNode": ListNode,
        "TreeNode": TreeNode,
    }
    exec(code, env)
    return env


def main():
    if len(sys.argv) < 4:
        print("Usage: python python_runner.py <solution_file> <function_name> <inputs_json> [mode]",
              file=sys.stderr)
        sys.exit(1)

    solution_file = sys.argv[1]
    function_name = sys.argv[2]
    inputs = json.loads(sys.argv[3])
    mode = sys.argv[4] if len(sys.argv) > 4 else "default"

    # Read solution code
    with open(solution_file) as f:
        code = f.read()

    env = _build_env(code)

    # Modes that manage their own class instantiation
    self_managed_modes = {"design", "codec", "codec_url", "first_bad_version",
                          "guess_number", "encode_decode", "linked_list_intersection"}

    if mode not in self_managed_modes:
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

    # --- Dispatch by mode ---
    if mode == "linked_list":
        converted = []
        for arg in inputs:
            if isinstance(arg, list):
                if not arg:
                    converted.append(list_to_linked(arg))
                elif isinstance(arg[0], (int, float)):
                    converted.append(list_to_linked(arg))
                elif isinstance(arg[0], list):
                    # List of linked lists (e.g. mergeKLists)
                    converted.append([list_to_linked(sub) for sub in arg])
                else:
                    converted.append(arg)
            else:
                converted.append(arg)
        result = method(*converted)
        if isinstance(result, ListNode):
            print(json.dumps(linked_to_list(result)))
        elif result is None:
            print(json.dumps([]))
        elif isinstance(result, bool):
            print(json.dumps(result))
        elif isinstance(result, (int, float)):
            print(json.dumps(result))
        else:
            print(json.dumps(result))

    elif mode == "linked_list_inplace":
        # In-place linked list mutation (e.g., reorderList)
        converted = []
        for arg in inputs:
            if isinstance(arg, list):
                if not arg:
                    converted.append(list_to_linked(arg))
                elif isinstance(arg[0], (int, float)):
                    converted.append(list_to_linked(arg))
                else:
                    converted.append(arg)
            else:
                converted.append(arg)
        method(*converted)
        first_ll = converted[0] if converted else None
        if isinstance(first_ll, ListNode):
            print(json.dumps(linked_to_list(first_ll)))
        else:
            print(json.dumps([]))

    elif mode == "tree":
        converted = []
        for arg in inputs:
            if isinstance(arg, list) and (not arg or arg[0] is None or isinstance(arg[0], (int, float))):
                converted.append(list_to_tree(arg))
            else:
                converted.append(arg)
        result = method(*converted)
        if isinstance(result, TreeNode) or result is None:
            print(json.dumps(tree_to_list(result)))
        elif isinstance(result, list):
            out = []
            for item in result:
                if isinstance(item, TreeNode):
                    out.append(tree_to_list(item))
                elif isinstance(item, list):
                    out.append(item)
                else:
                    out.append(item)
            print(json.dumps(out))
        else:
            print(json.dumps(result))

    elif mode == "tree_lca":
        # First arg is tree (list), remaining int args are node values to look up
        tree_arr = inputs[0]
        root = list_to_tree(tree_arr)

        def find_node(node, val):
            if not node:
                return None
            if node.val == val:
                return node
            return find_node(node.left, val) or find_node(node.right, val)

        converted = [root]
        for arg in inputs[1:]:
            if isinstance(arg, int):
                converted.append(find_node(root, arg))
            else:
                converted.append(arg)
        result = method(*converted)
        if isinstance(result, TreeNode):
            print(json.dumps(result.val))
        elif result is None:
            print(json.dumps(None))
        else:
            print(json.dumps(result))

    elif mode == "inplace":
        # For in-place functions: call the method, then return the first input (mutated)
        method(*inputs)
        print(json.dumps(inputs[0]))

    elif mode == "design":
        # Design class mode: inputs = [["ClassName","method1",...], [[args],[args],...]]
        # The function_name is used as the class name to find in the env
        operations = inputs[0]
        arguments = inputs[1]
        results = []
        class_name = operations[0]
        cls = env.get(class_name) or env.get("Solution")
        obj = cls(*arguments[0])
        results.append(None)
        for i in range(1, len(operations)):
            op = operations[i]
            args = arguments[i]
            m = getattr(obj, op)
            r = m(*args)
            results.append(r)
        print(json.dumps(results))

    elif mode == "first_bad_version":
        # inputs = [n, bad] - mock isBadVersion API
        n = inputs[0]
        bad = inputs[1]
        env["isBadVersion"] = lambda v, b=bad: v >= b
        sol = env["Solution"]()
        method = getattr(sol, function_name)
        result = method(n)
        print(json.dumps(result))

    elif mode == "guess_number":
        # inputs = [n, pick] - mock guess API
        n = inputs[0]
        pick = inputs[1]
        def guess_fn(num, p=pick):
            if num < p: return 1
            elif num > p: return -1
            else: return 0
        env["guess"] = guess_fn
        sol = env["Solution"]()
        method = getattr(sol, function_name)
        result = method(n)
        print(json.dumps(result))

    elif mode == "codec":
        # Serialize/Deserialize: input is tree as list, output should be same tree as list
        tree_arr = inputs[0]
        root = list_to_tree(tree_arr)
        codec = env.get("Codec")
        if codec is None:
            print(json.dumps(tree_arr))
        else:
            obj = codec()
            serialized = obj.serialize(root)
            deserialized = obj.deserialize(serialized)
            print(json.dumps(tree_to_list(deserialized)))

    elif mode == "codec_url":
        # Encode/Decode URL: input is url string, output should be same url
        url = inputs[0]
        codec = env.get("Codec")
        if codec is None:
            print(json.dumps(url))
        else:
            obj = codec()
            encoded = obj.encode(url)
            decoded = obj.decode(encoded)
            print(json.dumps(decoded))

    elif mode == "encode_decode":
        # Encode then decode strings: input is list of strings
        strs = inputs[0]
        sol = env["Solution"]()
        encoded = sol.encode(strs)
        decoded = sol.decode(encoded)
        print(json.dumps(decoded))

    elif mode == "linked_list_intersection":
        # inputs = [list1, list2, intersect_val]
        # For now, only handles non-intersecting case (intersect_val == -1)
        arr1 = inputs[0]
        arr2 = inputs[1]
        head1 = list_to_linked(arr1)
        head2 = list_to_linked(arr2)
        sol = env["Solution"]()
        method = getattr(sol, function_name)
        result = method(head1, head2)
        if result is None:
            print(json.dumps(None))
        else:
            print(json.dumps(result.val))

    else:
        # Default mode
        result = method(*inputs)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
