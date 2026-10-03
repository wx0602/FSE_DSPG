#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def parse_rules_text(text: str) -> List[Dict[str, str]]:
    """
    Parse rule text in the following structure (no PyYAML required):

    tasks:
      - target_id: CODEC-263_DBlog-master
        module: blog-core
        Dtest: PasswordUtil_ESTest
        poc_string: IllegalArgumentException
    """
    tasks = []
    current = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # New task starts
        if stripped.startswith("- "):
            if current:
                tasks.append(current)
            current = {}

            rest = stripped[2:].strip()
            if rest and ":" in rest:
                k, v = rest.split(":", 1)
                current[k.strip()] = v.strip()
            continue

        # Normal key: value line
        if current is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            current[k.strip()] = v.strip()

    if current:
        tasks.append(current)

    return tasks


def load_rules(rule_file: str) -> List[Dict[str, str]]:
    with open(rule_file, "r", encoding="utf-8") as f:
        text = f.read()

    tasks = parse_rules_text(text)
    if not tasks:
        raise ValueError(f"No tasks parsed from rule file: {rule_file}")

    # Basic validation
    cleaned = []
    for i, t in enumerate(tasks, 1):
        target_id = t.get("target_id", "").strip()
        dtest = t.get("Dtest", "").strip()
        if not target_id or not dtest:
            print(f"[WARN] Skipping task {i}: missing target_id or Dtest: {t}", file=sys.stderr)
            continue
        cleaned.append({
            "target_id": target_id,
            "module": t.get("module", "").strip(),
            "Dtest": dtest,
            "poc_string": t.get("poc_string", "").strip(),
        })

    if not cleaned:
        raise ValueError("No valid target_id / Dtest entries in rule file")

    return cleaned


def find_patch_files(root_dir: str) -> List[Path]:
    exts = {".patch", ".diff"}
    root = Path(root_dir)
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return files


def patch_belongs_to_target(patch_path: Path, target_id: str) -> bool:
    """
    Check if patch filename starts with target_id.
    Examples:
      CODEC-263_DBlog-master.patch
      CODEC-263_DBlog-master_001.diff
      CODEC-263_DBlog-master-anything.patch
    """
    return patch_path.name.startswith(target_id)


def patch_modifies_dtest(patch_path: Path, dtest_class: str) -> bool:
    """
    Check if patch modifies the corresponding Dtest.java file.
    Detects file paths/names in patch content.
    """
    java_name = f"{dtest_class}.java"

    # Match common patch path patterns
    # Example:
    #   diff --git a/.../PasswordUtil_ESTest.java b/.../PasswordUtil_ESTest.java
    #   --- a/.../PasswordUtil_ESTest.java
    #   +++ b/.../PasswordUtil_ESTest.java
    #   Index: .../PasswordUtil_ESTest.java
    pattern = re.compile(rf'(^|[\\/]){re.escape(java_name)}($|[\t \r\n])')

    try:
        content = patch_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] Failed to read, skipping {patch_path}: {e}", file=sys.stderr)
        return False

    # Quick check
    if java_name not in content:
        return False

    # Accurate regex check
    if pattern.search(content):
        return True

    # Fallback: loose match
    return java_name in content


def analyze(root_dir: str, rules: List[Dict[str, str]]) -> Tuple[int, Dict[str, List[str]]]:
    patch_files = find_patch_files(root_dir)

    matched: Dict[str, List[str]] = {}

    for task in rules:
        target_id = task["target_id"]
        dtest = task["Dtest"]

        for patch in patch_files:
            if not patch_belongs_to_target(patch, target_id):
                continue

            if patch_modifies_dtest(patch, dtest):
                matched.setdefault(target_id, []).append(str(patch))

    total_patch_count = sum(len(v) for v in matched.values())
    return total_patch_count, matched


def main():
    parser = argparse.ArgumentParser(
        description="Count how many patch/diff files modify the corresponding Dtest.java defined in rules"
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Root directory to scan recursively for .patch / .diff files"
    )
    parser.add_argument(
        "--rules",
        required=True,
        help="Path to rule file (YAML-like tasks format)"
    )
    parser.add_argument(
        "--show-files",
        action="store_true",
        help="Show full paths of matched patch files"
    )

    args = parser.parse_args()

    rules = load_rules(args.rules)
    total_patch_count, matched = analyze(args.dir, rules)

    print(f"Total patches modifying corresponding Dtest: {total_patch_count}")
    print(f"Matched target_id count: {len(matched)}")
    print()

    if matched:
        print("Matched target_id list:")
        for target_id in sorted(matched.keys()):
            print(f"  {target_id} ({len(matched[target_id])})")
            if args.show_files:
                for fp in matched[target_id]:
                    print(f"    - {fp}")
    else:
        print("No patches modified the corresponding Dtest files.")


if __name__ == "__main__":
    main()

