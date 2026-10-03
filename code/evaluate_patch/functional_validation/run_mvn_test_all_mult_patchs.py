#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def enable_ansi_on_windows() -> None:
    if os.name == "nt":
        try:
            os.system("")
        except Exception:
            pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch invoke run_mvn_test_one.py for agentless_patch multi-patch directories."
    )
    parser.add_argument(
        "--patchs",
        required=True,
        help="Root directory containing target_id subdirectories, each with multiple patch files",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Root directory for repositories, e.g. /VESTA/resource/",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory. Successful patches will be copied to output/<target_id>/",
    )
    parser.add_argument(
        "--repo_copy_root",
        default="/tmp/tmp_repo",
        help="Root directory for temporary repo copies, default: /tmp/tmp_repo",
    )
    parser.add_argument(
        "--run_script",
        default="run_mvn_test_one.py",
        help="Path to run_mvn_test_one.py",
    )
    parser.add_argument(
        "--patch_suffixes",
        nargs="*",
        default=[".patch", ".diff"],
        help="Patch file suffixes to include, default: .patch .diff",
    )
    return parser.parse_args()


def is_patch_file(filename: str, suffixes: List[str]) -> bool:
    lower = filename.lower()
    return any(lower.endswith(s.lower()) for s in suffixes)


def find_target_dirs(patch_root: str) -> List[Path]:
    """
    Find first-level subdirectories under patch_root.
    Each subdirectory name is treated as one target_id.
    """
    root = Path(patch_root)
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"--patchs is not a valid directory: {patch_root}")

    dirs = [p for p in root.iterdir() if p.is_dir()]
    dirs.sort(key=lambda x: x.name)
    return dirs


def find_patch_files_in_target_dir(target_dir: Path, suffixes: List[str]) -> List[Path]:
    """
    Recursively find patch files inside one target_id directory.
    """
    patch_files = []
    for dirpath, _, filenames in os.walk(target_dir):
        for filename in filenames:
            if is_patch_file(filename, suffixes):
                patch_files.append(Path(dirpath) / filename)

    patch_files.sort(key=lambda x: str(x))
    return patch_files


def parse_target_id_to_repo_paths(target_id: str, repo_root: str, repo_copy_root: str) -> Tuple[str, str, str, str]:
    """
    target_id comes from folder name directly.
    Example:
      target_id = CODEC-263_DBlog-master

    Split by the first underscore:
      part1 = CODEC-263
      part2 = DBlog-master

    Then:
      repo_path = <repo_root>/CODEC-263/DBlog-master
      repo_copy_path = <repo_copy_root>/CODEC-263/DBlog-master
    """
    if "_" not in target_id:
        raise ValueError(f"Invalid target_id (no underscore found): {target_id}")

    part1, part2 = target_id.split("_", 1)
    repo_path = os.path.join(repo_root, part1, part2)
    repo_copy_path = os.path.join(repo_copy_root, part1, part2)
    return part1, part2, repo_path, repo_copy_path


def run_test_script(
    run_script: str,
    target_id: str,
    patch_path: str,
    repo_path: str,
    repo_copy_path: str,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        run_script,
        f"--target_id={target_id}",
        f"--patch={patch_path}",
        f"--repo={repo_path}",
        f"--repo_copy={repo_copy_path}",
    ]

    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def parse_result(stdout_text: str, return_code: int) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Parse __RESULT_JSON__ from run_mvn_test_one.py output.
    Fallback:
      return_code == 0 => success
      otherwise => fail
    """
    result_json = None
    parse_error = None

    for line in stdout_text.splitlines():
        if line.startswith("__RESULT_JSON__="):
            try:
                result_json = json.loads(line.split("=", 1)[1])
                success = bool(result_json.get("success", False))
                return success, result_json, None
            except Exception as e:
                parse_error = str(e)
                break

    success = (return_code == 0)
    return success, result_json, parse_error


def copy_success_patch(patch_path: str, output_root: str, target_id: str) -> str:
    """
    Copy successful original patch to:
      output/<target_id>/<patch_filename>
    """
    target_output_dir = Path(output_root) / target_id
    target_output_dir.mkdir(parents=True, exist_ok=True)

    dst = target_output_dir / Path(patch_path).name
    shutil.copy2(patch_path, dst)
    return str(dst)


def print_one_result(result: Dict) -> None:
    if result["success"]:
        status_text = f"{GREEN}SUCCESS{RESET}"
    else:
        status_text = f"{RED}FAIL{RESET}"

    print(
        f"{CYAN}[BATCH RESULT]{RESET} "
        f"target_id={result['target_id']} "
        f"patch={result['patch_name']} "
        f"status={status_text}"
    )


def print_summary(results: List[Dict]) -> None:
    success_results = [r for r in results if r["success"]]
    fail_results = [r for r in results if not r["success"]]

    print("\n========== FINAL SUMMARY ==========")

    print(f"{GREEN}SUCCESS PATCHES:{RESET}")
    if success_results:
        for r in success_results:
            print(
                f"  - target_id={r['target_id']} "
                f"patch={r['patch_name']} "
                f"repo={r['repo_path']}"
            )
    else:
        print("  (none)")

    print(f"\n{RED}FAIL PATCHES:{RESET}")
    if fail_results:
        for r in fail_results:
            print(
                f"  - target_id={r['target_id']} "
                f"patch={r['patch_name']} "
                f"repo={r['repo_path']}"
            )
    else:
        print("  (none)")

    success_count = len(success_results)
    fail_count = len(fail_results)
    total_count = len(results)

    print("\n========== COUNTS ==========")
    print(f"TOTAL   : {total_count}")
    print(f"SUCCESS : {success_count}")
    print(f"FAIL    : {fail_count}")


def main():
    enable_ansi_on_windows()
    args = parse_args()

    patch_root = args.patchs
    repo_root = args.repo
    output_root = args.output
    repo_copy_root = args.repo_copy_root
    run_script = args.run_script
    patch_suffixes = args.patch_suffixes

    os.makedirs(output_root, exist_ok=True)

    target_dirs = find_target_dirs(patch_root)
    print(f"[INFO] Found {len(target_dirs)} target directories under: {patch_root}")

    all_results: List[Dict] = []

    for target_dir in target_dirs:
        target_id = target_dir.name

        print(f"\n{'=' * 80}")
        print(f"[INFO] Processing target_id: {target_id}")

        try:
            _, _, repo_path, repo_copy_path = parse_target_id_to_repo_paths(
                target_id=target_id,
                repo_root=repo_root,
                repo_copy_root=repo_copy_root,
            )
        except Exception as e:
            print(f"{YELLOW}[WARN]{RESET} Skip invalid target directory: {target_id}, reason: {e}")
            continue

        patch_files = find_patch_files_in_target_dir(target_dir, patch_suffixes)
        print(f"[INFO] Found {len(patch_files)} patch file(s) in: {target_dir}")

        if not patch_files:
            print(f"{YELLOW}[WARN]{RESET} No patch files found under target directory: {target_dir}")
            continue

        for patch_file in patch_files:
            patch_path = str(patch_file)
            patch_name = patch_file.name

            print(f"\n[INFO] Running patch: {patch_name}")
            print(f"[INFO] target_id={target_id}")
            print(f"[INFO] patch={patch_path}")
            print(f"[INFO] repo={repo_path}")
            print(f"[INFO] repo_copy={repo_copy_path}")

            res = run_test_script(
                run_script=run_script,
                target_id=target_id,
                patch_path=patch_path,
                repo_path=repo_path,
                repo_copy_path=repo_copy_path,
            )

            print(res.stdout)

            success, result_json, parse_error = parse_result(res.stdout, res.returncode)

            copied_to = None
            if success:
                copied_to = copy_success_patch(
                    patch_path=patch_path,
                    output_root=output_root,
                    target_id=target_id,
                )

            record = {
                "target_id": target_id,
                "patch_name": patch_name,
                "patch_path": patch_path,
                "repo_path": repo_path,
                "repo_copy_path": repo_copy_path,
                "success": success,
                "return_code": res.returncode,
                "parse_error": parse_error,
                "result_json": result_json,
                "copied_to": copied_to,
            }

            print_one_result(record)
            all_results.append(record)

    print_summary(all_results)

    summary_path = os.path.join(output_root, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n[INFO] Summary written to: {summary_path}")


if __name__ == "__main__":
    main()
