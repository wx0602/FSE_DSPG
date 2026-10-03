#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from collections import defaultdict


def parse_rules(rule_path: str):
    """
    Parse a rule file in the following format (no PyYAML required):

    tasks:
      - target_id: CODEC-263_DBlog-master
        module: blog-core
        Dtest: PasswordUtil_ESTest
        poc_string: IllegalArgumentException

      - target_id: CODEC-270_BurpCrypto-master
        module: .
        Dtest: AesUtil_ESTest
        poc_string: NullPointerException

    Returns:
        {
            "CODEC-263_DBlog-master": {
                "module": "blog-core",
                "dtest": "PasswordUtil_ESTest",
                "dtest_java": "PasswordUtil_ESTest.java"
            },
            ...
        }
    """
    with open(rule_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    tasks = []
    current = None

    key_value_re = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$')

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith("#"):
            continue

        stripped = line.strip()

        # Start of a new task
        if stripped.startswith("- "):
            if current:
                tasks.append(current)
            current = {}

            rest = stripped[2:].strip()
            # Support format "- target_id: xxx"
            if rest:
                m = key_value_re.match(rest)
                if m:
                    key, value = m.group(1), m.group(2)
                    current[key] = strip_quotes(value)
            continue

        # Normal key: value line
        m = key_value_re.match(line)
        if m and current is not None:
            key, value = m.group(1), m.group(2)
            current[key] = strip_quotes(value)

    if current:
        tasks.append(current)

    rules = {}
    for task in tasks:
        target_id = task.get("target_id")
        dtest = task.get("Dtest")
        module = task.get("module", "")
        if not target_id or not dtest:
            continue

        rules[target_id] = {
            "module": module,
            "dtest": dtest,
            "dtest_java": f"{dtest}.java",
        }

    return rules


def strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1]
    return s


def find_target_for_folder(folder_name: str, target_ids):
    """
    Match folder_name -> target_id using "longest prefix first" rule.
    Avoid conflicts between prefixes like CODEC-26 and CODEC-263.
    """
    matched = [tid for tid in target_ids if folder_name.startswith(tid)]
    if not matched:
        return None
    return max(matched, key=len)


def is_patch_file(path: str) -> bool:
    """
    Lenient patch file check:
    - Common extensions: .patch / .diff
    - Also try reading regular text files
    """
    if not os.path.isfile(path):
        return False
    return True


def patch_modifies_dtest(patch_path: str, dtest_java: str) -> bool:
    """
    Check if the patch modifies the target Dtest.java file.
    Matches common patch path lines, e.g.:
      diff --git a/.../PasswordUtil_ESTest.java b/.../PasswordUtil_ESTest.java
      --- a/.../PasswordUtil_ESTest.java
      +++ b/.../PasswordUtil_ESTest.java
      Index: .../PasswordUtil_ESTest.java
    """
    try:
        with open(patch_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()

                if (
                    s.startswith("diff --git ")
                    or s.startswith("--- ")
                    or s.startswith("+++ ")
                    or s.startswith("Index: ")
                    or s.startswith("*** ")
                ):
                    if dtest_java in s:
                        return True

                # Fallback: some patches have non-standard paths but contain the filename
                if dtest_java in s and ("/" in s or "\\" in s):
                    return True

    except Exception as e:
        print(f"[WARN] Failed to read file: {patch_path}, error={e}", file=sys.stderr)

    return False


def scan(root_dir: str, rules: dict):
    """
    Scan all first-level subdirectories (patch folders) under root_dir.
    Returns:
        hit_map = {
            target_id: [patch_file1, patch_file2, ...]
        }
    """
    target_ids = list(rules.keys())
    hit_map = defaultdict(list)

    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"Not a directory: {root_dir}")

    for entry in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, entry)
        if not os.path.isdir(folder_path):
            continue

        target_id = find_target_for_folder(entry, target_ids)
        if not target_id:
            continue

        dtest_java = rules[target_id]["dtest_java"]

        # Recursively scan all files in this patch folder
        for dirpath, _, filenames in os.walk(folder_path):
            for filename in filenames:
                patch_path = os.path.join(dirpath, filename)
                if not is_patch_file(patch_path):
                    continue

                if patch_modifies_dtest(patch_path, dtest_java):
                    rel_path = os.path.relpath(patch_path, folder_path)
                    hit_map[target_id].append(rel_path)

    return hit_map


def main():
    parser = argparse.ArgumentParser(
        description="Count how many target_id folders have patches modifying their corresponding Dtest.java"
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Root directory containing many patch folders"
    )
    parser.add_argument(
        "--rules",
        required=True,
        help="Path to rule file (YAML-like tasks format)"
    )
    args = parser.parse_args()

    rules = parse_rules(args.rules)
    if not rules:
        print("No target_id / Dtest entries parsed from rule file", file=sys.stderr)
        sys.exit(1)

    hit_map = scan(args.dir, rules)

    # Deduplicate and sort
    normalized = {}
    for target_id, files in hit_map.items():
        normalized[target_id] = sorted(set(files))

    print("=" * 80)
    print(f"Number of target_id folders with modified Dtest: {len(normalized)}")
    print("=" * 80)

    for target_id in sorted(normalized.keys()):
        dtest_java = rules[target_id]["dtest_java"]
        print(f"\n[target_id] {target_id}")
        print(f"[Dtest]    {dtest_java}")
        print(f"[patches]  {len(normalized[target_id])}")
        for patch_name in normalized[target_id]:
            print(f"  - {patch_name}")


if __name__ == "__main__":
    main()

