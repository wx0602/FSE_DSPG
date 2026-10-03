#!/usr/bin/env python3
"""
Batch driver to invoke run_mvn_test_one.py over multiple patch files.

Example:
  python batch_run_mvn_tests.py --patchs /path/to/patches \
      --repo /path/to/repos --output /path/to/output
"""
import argparse
import json
import os
import sys
import shutil
import subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Batch invoke run_mvn_test_one.py for multiple patches.")
    parser.add_argument("--patchs", required=True, help="Root directory containing patch files")
    parser.add_argument("--repo", required=True, help="Root directory for repositories")
    parser.add_argument("--output", required=True, help="Directory to copy successful patches and summary")
    parser.add_argument("--repo_copy_root", default="/tmp/tmp_repo", help="Root path for temp repo copies")
    parser.add_argument("--run_script", default="run_mvn_test_one.py", help="Path to run_mvn_test_one.py script")
    return parser.parse_args()

def find_patch_files(root):
    """Recursively find patch or diff files under the given directory."""
    patch_files = []
    for dirpath, dirs, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".patch") or f.lower().endswith(".diff"):
                patch_files.append(os.path.join(dirpath, f))
    return patch_files

def run_mvn_test(run_script, target_id, patch_path, repo_path, repo_copy_path):
    """
    Invoke the run_mvn_test_one.py script for one patch.
    Returns a subprocess-like result object with .stdout and .returncode.
    """
    cmd = [sys.executable, run_script,
           f"--target_id={target_id}",
           f"--patch={patch_path}",
           f"--repo={repo_path}",
           f"--repo_copy={repo_copy_path}"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return result
    except Exception as e:
        # If subprocess launch fails, return a dummy result with error info
        class Dummy:
            pass
        r = Dummy()
        r.returncode = -1
        r.stdout = f"Exception when running subprocess: {e}"
        return r

def main():
    args = parse_args()
    patch_root = args.patchs
    repo_root = args.repo
    output_dir = args.output
    repo_copy_root = args.repo_copy_root
    run_script = args.run_script

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # ANSI color codes for terminal output
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    # Find patch files under the given directory
    patch_files = find_patch_files(patch_root)
    results = []
    print(f"[INFO] Found {len(patch_files)} patch files under {patch_root}")

    for patch_path in patch_files:
        patch_name = os.path.basename(patch_path)

        # Derive target_id by splitting filename at the first underscore.
        # E.g. "Lang_1.patch" -> first="Lang", second="1".
        if "_" not in patch_name:
            print(f"[WARN] Skipping patch {patch_name} (no underscore in name)")
            results.append({
                "patch_file": patch_name,
                "target_id": None,
                "repo": None,
                "result": "SKIPPED",
                "success": False
            })
            continue

        base, ext = os.path.splitext(patch_name)
        parts = base.split("_", 1)
        if len(parts) < 2:
            print(f"[WARN] Skipping patch {patch_name} (unexpected format)")
            results.append({
                "patch_file": patch_name,
                "target_id": None,
                "repo": None,
                "result": "SKIPPED",
                "success": False
            })
            continue

        first, second = parts[0], parts[1]
        target_id = f"{first}-{second}"
        # Construct the repository path. Assumption: repo is at <repo_root>/<first>/<second>.
        # For example, if first="Lang" and second="1", then repo_path = os.path.join(repo_root, "Lang", "1").
        repo_path = os.path.join(repo_root, first, second)
        # Temporary copy directory for this target
        repo_copy_path = os.path.join(repo_copy_root, target_id)

        print(f"[INFO] Processing patch {patch_name}: target_id={target_id}, repo_path={repo_path}")

        # Invoke the existing test script for this patch
        result = run_mvn_test(run_script, target_id, patch_path, repo_path, repo_copy_path)
        output = result.stdout
        rc = result.returncode

        # Attempt to parse JSON output (looks for "__RESULT_JSON__=..." line).
        success = False
        json_data = None
        parse_error = None
        for line in output.splitlines():
            if line.startswith("__RESULT_JSON__="):
                try:
                    json_data = json.loads(line.split("=", 1)[1])
                    success = json_data.get("success", False)
                except Exception as e:
                    parse_error = str(e)
                    success = False
                break
        else:
            # No JSON found; use exit code: 0=success, else failure
            success = (rc == 0)

        # Record the result
        entry = {
            "patch_file": patch_name,
            "target_id": target_id,
            "repo": repo_path,
            "success": success
        }
        if json_data is None:
            # If JSON not available, include the exit code and parse error
            entry["exit_code"] = rc
            if parse_error:
                entry["parse_error"] = parse_error

        results.append(entry)

        # If successful, copy the patch file to the output directory
        if success:
            try:
                shutil.copy(patch_path, output_dir)
            except Exception as e:
                print(f"[ERROR] Failed to copy {patch_name} to output: {e}")

    # Print a summary table to the console
    if results:
        print()
        col1 = "Patch File"
        col2 = "Target ID"
        col3 = "Repo Path"
        col4 = "Result"
        width1 = max(len(str(r.get("patch_file",""))) for r in results) + 2
        width2 = max(len(str(r.get("target_id") or "")) for r in results) + 2
        width3 = max(len(str(r.get("repo") or "")) for r in results) + 2
        width4 = len(col4) + 2
        header = f"{col1:<{width1}}{col2:<{width2}}{col3:<{width3}}{col4:<{width4}}"
        print(header)
        print("-" * (width1+width2+width3+width4))

        for entry in results:
            patch_file = entry["patch_file"]
            target_id = entry.get("target_id") or ""
            repo = entry.get("repo") or ""
            success = entry["success"]
            # Determine the result text and color
            if entry.get("result") == "SKIPPED":
                res_text = "SKIPPED"
                color = YELLOW
            elif success:
                res_text = "SUCCESS"
                color = GREEN
            else:
                code = entry.get("exit_code", 1)
                if code == 1:
                    res_text = "FAIL"
                else:
                    res_text = "ERROR"
                color = RED
            print(f"{patch_file:<{width1}}{target_id:<{width2}}{repo:<{width3}}"
                  f"{color}{res_text:<{width4}}{RESET}")

    # Write the JSON summary file
    summary_path = os.path.join(output_dir, "summary.json")
    try:
        with open(summary_path, "w") as sf:
            json.dump(results, sf, indent=2)
        print(f"[INFO] Summary written to {summary_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write summary: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
