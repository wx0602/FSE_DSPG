#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

DIFF_START_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)\s*$")
HUNK_RE = re.compile(r"^@@\s+[-]\d+(?:,\d+)?\s+[+]\d+(?:,\d+)?\s+@@")
JAVA_FILE_RE = re.compile(r".*\.java$", re.IGNORECASE)

METHOD_DECL_RE = re.compile(
    r"""^\s*(?:public|protected|private)?\s*
         (?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:native\s+)?(?:abstract\s+)?
         [\w\<\>\[\],\s\.\?]+\s+([A-Za-z_]\w*)\s*\(
     """,
    re.VERBOSE,
)
TEST_ANNOT_RE = re.compile(r"^\s*@Test\b")


@dataclass
class RemovedTestInfo:
    file_path: str
    functions: List[str] = field(default_factory=list)


@dataclass
class PatchReport:
    patch_name: str
    is_empty: bool
    had_test_changes: bool
    removed_tests: List[RemovedTestInfo] = field(default_factory=list)


def is_test_java_filename(path: str) -> bool:
    base = os.path.basename(path)
    return bool(JAVA_FILE_RE.match(base)) and ("test" in base.lower())


def compute_is_empty_patch(lines: List[str]) -> bool:
    has_diff = any(l.startswith("diff --git ") for l in lines)
    if not has_diff:
        return True

    change_lines = 0
    for l in lines:
        if l.startswith("+++ ") or l.startswith("--- "):
            continue
        if l.startswith("+") or l.startswith("-"):
            if l.startswith(r"\ No newline"):
                continue
            change_lines += 1
    return change_lines == 0


def split_file_sections(lines: List[str]) -> List[Tuple[Optional[str], List[str]]]:
    sections: List[Tuple[Optional[str], List[str]]] = []
    cur: List[str] = []
    cur_path: Optional[str] = None

    def flush():
        nonlocal cur, cur_path
        if cur:
            sections.append((cur_path, cur))
        cur = []
        cur_path = None

    for line in lines:
        m = DIFF_START_RE.match(line)
        if m:
            flush()
            cur_path = m.group(2)
            cur.append(line)
        else:
            cur.append(line)
    flush()
    return sections


def extract_test_functions_from_section(section_lines: List[str]) -> List[str]:
    functions: List[str] = []
    seen = set()
    pending_test_annot = False

    def add_fn(name: str):
        if name and name not in seen:
            seen.add(name)
            functions.append(name)

    for raw in section_lines:
        line = raw
        stripped = line[1:] if line[:1] in (" ", "+", "-") else line
        stripped = stripped.rstrip("\n")

        if TEST_ANNOT_RE.match(stripped):
            pending_test_annot = True
            continue

        mm = METHOD_DECL_RE.match(stripped)
        if mm:
            fn = mm.group(1)
            if pending_test_annot:
                add_fn(fn)
                pending_test_annot = False
            else:
                add_fn(fn)

    return functions


def remove_test_java_sections_and_report(patch_path: str, out_path: str) -> PatchReport:
    with open(patch_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    empty = compute_is_empty_patch(lines)
    sections = split_file_sections(lines)

    kept_lines: List[str] = []
    removed: List[RemovedTestInfo] = []

    for b_path, sec in sections:
        if b_path is None:
            kept_lines.extend(sec)
            continue

        if is_test_java_filename(b_path):
            funcs = extract_test_functions_from_section(sec)
            removed.append(RemovedTestInfo(file_path=b_path, functions=funcs))
            
        else:
            kept_lines.extend(sec)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", errors="replace", newline="") as f:
        f.writelines(kept_lines)

    return PatchReport(
        patch_name=os.path.basename(patch_path),
        is_empty=empty,
        had_test_changes=(len(removed) > 0),
        removed_tests=removed,
    )


def main():
    ap = argparse.ArgumentParser(
        description="Detect empty patches, remove test*.java changes, output to new directory and print statistics."
    )
    ap.add_argument("--input_patchs", required=True, help="Input directory containing .patch/.diff files")
    ap.add_argument("--output_patchs", required=True, help="Output directory (keep original filenames)")
    ap.add_argument(
        "--ext",
        default=".patch,.diff",
        help="File extensions to process (comma separated, default: .patch,.diff)",
    )
    args = ap.parse_args()

    input_dir = args.input_patchs
    output_dir = args.output_patchs

    exts = {e.strip().lower() for e in args.ext.split(",") if e.strip()}
    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(2)

    os.makedirs(output_dir, exist_ok=True)

    patch_files = []
    for name in os.listdir(input_dir):
        p = os.path.join(input_dir, name)
        if not os.path.isfile(p):
            continue
        lower = name.lower()
        if any(lower.endswith(ext) for ext in exts):
            patch_files.append(p)
    patch_files.sort()

    reports: List[PatchReport] = []
    empty_patches: List[str] = []

    for p in patch_files:
        out_p = os.path.join(output_dir, os.path.basename(p))
        rep = remove_test_java_sections_and_report(p, out_p)
        reports.append(rep)
        if rep.is_empty:
            empty_patches.append(rep.patch_name)

    patches_with_test = [r for r in reports if r.had_test_changes]

    print("========== SCAN RESULT ==========")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Total patch files: {len(reports)}")
    print(f"Empty patches: {len(empty_patches)}")
    if empty_patches:
        print("Empty patch list:")
        for n in empty_patches:
            print(f"  - {n}")

    print()
    print(f"Patches containing test*.java changes: {len(patches_with_test)}")
    if not patches_with_test:
        return

    print()
    print("========== DETAILS (Patch | Test File | Test Functions) ==========")
    for r in patches_with_test:
        print(f"\n[Patch] {r.patch_name}")
        for t in r.removed_tests:
            print(f"  - Test file: {t.file_path}")
            if t.functions:
                print("    Related test functions:")
                for fn in t.functions:
                    print(f"      * {fn}")
            else:
                print("    Related test functions: (not detected in diff)")


if __name__ == "__main__":
    main()

