#!/usr/bin/env python3
"""
Modify a single parameter value in a ROS 2 YAML parameter file.

Usage:
    python3 modify_param.py <input.yaml> <output.yaml> <yaml_path> <value> [--type TYPE]

The yaml_path uses '/' as separator and the leading '/**/' prefix is stripped.
Example:
    python3 modify_param.py base.yaml modified.yaml \
        "/**/ros__parameters/ndt/resolution" 4.0 --type float
"""

import argparse
import copy
import sys
import yaml


def set_nested_value(d: dict, keys: list[str], value) -> bool:
    """Walk into dict `d` along `keys`, set the final key to `value`."""
    for key in keys[:-1]:
        if key not in d:
            return False
        d = d[key]
        if not isinstance(d, dict):
            return False
    final_key = keys[-1]
    if final_key in d:
        d[final_key] = value
        return True
    return False


def find_and_set(d: dict, keys: list[str], value) -> bool:
    """Recursively search for the key path in nested dicts (handles wildcards)."""
    if not keys:
        return False

    if len(keys) == 1:
        if keys[0] in d:
            d[keys[0]] = value
            return True
        for k, v in d.items():
            if isinstance(v, dict):
                if find_and_set(v, keys, value):
                    return True
        return False

    key = keys[0]
    if key in d and isinstance(d[key], dict):
        if find_and_set(d[key], keys[1:], value):
            return True

    for k, v in d.items():
        if isinstance(v, dict):
            if find_and_set(v, keys, value):
                return True

    return False


def parse_yaml_path(path: str) -> list[str]:
    """Convert a YAML path like '/**/ros__parameters/ndt/resolution' to key list."""
    path = path.strip("/")
    parts = [p for p in path.split("/") if p and p != "**"]
    return parts


def cast_value(value_str: str, type_hint: str = "auto"):
    """Cast a string value to the appropriate Python type."""
    if type_hint == "bool":
        return value_str.lower() in ("true", "1", "yes")
    if type_hint == "int":
        return int(value_str)
    if type_hint == "float":
        return float(value_str)
    if type_hint == "str":
        return value_str
    # auto-detect
    if value_str.lower() in ("true", "false"):
        return value_str.lower() == "true"
    try:
        val = int(value_str)
        return val
    except ValueError:
        pass
    try:
        val = float(value_str)
        return val
    except ValueError:
        pass
    return value_str


def main():
    parser = argparse.ArgumentParser(description="Modify a ROS 2 YAML parameter")
    parser.add_argument("input", help="Input YAML file")
    parser.add_argument("output", help="Output YAML file")
    parser.add_argument("yaml_path", help="Parameter path (e.g. /**/ros__parameters/ndt/resolution)")
    parser.add_argument("value", help="New value")
    parser.add_argument("--type", default="auto", choices=["auto", "int", "float", "bool", "str"],
                        help="Type hint for the value")
    args = parser.parse_args()

    # Some Autoware param files contain multiple YAML documents (separated by '---').
    # Load all documents, try to apply the change to each in turn, and write them back.
    with open(args.input, "r") as f:
        try:
            docs = list(yaml.safe_load_all(f))
        except yaml.YAMLError as e:
            print(f"ERROR: Failed to parse YAML: {args.input}", file=sys.stderr)
            print(str(e), file=sys.stderr)
            sys.exit(1)

    if not docs:
        print(f"ERROR: Empty or invalid YAML: {args.input}", file=sys.stderr)
        sys.exit(1)

    keys = parse_yaml_path(args.yaml_path)
    new_value = cast_value(args.value, args.type)

    modified_docs = copy.deepcopy(docs)
    changed = False
    for i, doc in enumerate(modified_docs):
        if isinstance(doc, dict) and find_and_set(doc, keys, new_value):
            changed = True
            break

    if not changed:
        print(f"ERROR: Path not found: {args.yaml_path}", file=sys.stderr)
        print(f"  Keys searched: {keys}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w") as f:
        if len(modified_docs) == 1:
            yaml.dump(modified_docs[0], f, default_flow_style=False, sort_keys=False)
        else:
            yaml.dump_all(modified_docs, f, default_flow_style=False, sort_keys=False)

    print(f"OK: {args.yaml_path} = {new_value} ({type(new_value).__name__})")


if __name__ == "__main__":
    main()
