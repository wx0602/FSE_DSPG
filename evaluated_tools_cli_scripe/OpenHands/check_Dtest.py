#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow:
1) Create repo_copy folder; copy everything from repo except .git into repo_copy
2) git init in repo_copy; add+commit as the baseline (first commit)
3) Run mvn tests in repo_copy/<module> before patch; print output; count poc_string occurrences from target/surefire-reports
4) Apply patch (git apply) at repo_copy root
5) Run mvn tests again; print output; count occurrences from target/surefire-reports
6) Print a pink table: rows = origin_repo, <patch_basename>; column = poc_string match count
7) Reset repo_copy back to the baseline commit; repo_copy is NOT deleted
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple


PINK = "\033[95m"   # light magenta / pink-ish
BLUE = "\033[94m"   # blue
RESET = "\033[0m"


def run_cmd(cmd, cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return CompletedProcess (non-streaming)."""
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def run_cmd_stream_and_capture(cmd, cwd: Path) -> Tuple[int, str]:
    """
    Run a command, stream stdout/stderr to console for manual verification,
    and also capture combined output for later logging.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )

    combined = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        combined.append(line)
    proc.wait()
    return proc.returncode, "".join(combined)


def count_occurrences(haystack: str, needle: str) -> int:
    """Count case-insensitive substring occurrences, including overlaps."""
    h = haystack.lower()
    n = needle.lower()
    if not n:
        return 0
    count = 0
    start = 0
    while True:
        idx = h.find(n, start)
        if idx == -1:
            break
        count += 1
        start = idx + 1  # allow overlap
    return count


def copy_repo_without_git(src_repo: Path, dst_repo_copy: Path) -> None:
    """Copy all files from src_repo to dst_repo_copy excluding .git directory."""
    if not src_repo.is_dir():
        raise FileNotFoundError(f"--repo is not a directory: {src_repo}")

    if dst_repo_copy.exists():
        raise FileExistsError(f"--repo_copy already exists: {dst_repo_copy}")

    dst_repo_copy.mkdir(parents=True, exist_ok=False)

    for item in src_repo.iterdir():
        if item.name == ".git":
            continue
        dest = dst_repo_copy / item.name
        if item.is_dir():
            shutil.copytree(item, dest, symlinks=True)
        else:
            shutil.copy2(item, dest)


def git_init_and_first_commit(repo_copy: Path) -> str:
    """Initialize git repo and create the first commit; return the commit hash."""
    run_cmd(["git", "init"], cwd=repo_copy, check=True)

    # Ensure commit works even if global git identity is not set
    run_cmd(["git", "config", "user.email", "auto@example.com"], cwd=repo_copy)
    run_cmd(["git", "config", "user.name", "git-auto"], cwd=repo_copy)

    run_cmd(["git", "add", "-A"], cwd=repo_copy, check=True)
    run_cmd(["git", "commit", "-m", "git auto first"], cwd=repo_copy, check=True)

    cp = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_copy, check=True)
    return cp.stdout.strip()


def git_apply_patch(repo_copy: Path, patch_path: Path) -> None:
    """Apply a patch file to repo_copy using git apply."""
    if not patch_path.is_file():
        raise FileNotFoundError(f"--patch is not a file: {patch_path}")

    run_cmd(["git", "apply", str(patch_path.resolve())], cwd=repo_copy, check=True)


def git_reset_hard(repo_copy: Path, commit_hash: str) -> None:
    """Reset repo_copy to a specific commit hash."""
    run_cmd(["git", "reset", "--hard", commit_hash], cwd=repo_copy, check=True)


def clear_surefire_reports(module_dir: Path) -> None:
    """
    Remove target/surefire-reports to avoid mixing previous runs.
    This does not affect the source repository.
    """
    reports_dir = module_dir / "target" / "surefire-reports"
    if reports_dir.exists():
        shutil.rmtree(reports_dir)


def read_surefire_text(module_dir: Path) -> str:
    """
    Read all files under target/surefire-reports as bytes and decode best-effort.
    This is intentionally broad (xml/txt/dumps) to catch the target string.
    """
    reports_dir = module_dir / "target" / "surefire-reports"
    if not reports_dir.exists():
        return ""

    chunks = []
    for p in sorted(reports_dir.rglob("*")):
        if not p.is_file():
            continue
        try:
            data = p.read_bytes()
            # Best-effort decoding; ignore errors to handle mixed encodings
            chunks.append(data.decode("utf-8", errors="ignore"))
        except Exception:
            # Skip unreadable files
            continue
    return "\n".join(chunks)


def run_mvn_and_count_from_surefire(label: str, mvn_cmd, module_dir: Path, poc_string: str) -> Tuple[int, int]:
    """
    Print a blue preface line, run Maven tests with streaming output,
    then count occurrences of poc_string from target/surefire-reports.
    Returns: (mvn_exit_code, poc_count)
    """
    clear_surefire_reports(module_dir)

    cmd_str = " ".join(mvn_cmd)
    print(f"{BLUE}[RUN] {label} :: {cmd_str}{RESET}")

    rc, _combined_output = run_cmd_stream_and_capture(mvn_cmd, cwd=module_dir)
    print(f"\n[INFO] mvn exit code ({label}): {rc}")

    surefire_text = read_surefire_text(module_dir)
    poc_count = count_occurrences(surefire_text, poc_string)
    print(f"[INFO] poc_string occurrences from target/surefire-reports ({label}): {poc_count}")
    print()
    return rc, poc_count


def print_pink_table(row_labels, col_label, values):
    """
    Print a simple pink table:
    rows: row_labels
    column: col_label
    values: list of ints aligned with row_labels
    """
    row_w = max(len("row"), max(len(r) for r in row_labels))
    col_w = max(len(col_label), max(len(str(v)) for v in values))

    top = f"+-{'-'*row_w}-+-{'-'*col_w}-+"
    hdr = f"| {'row'.ljust(row_w)} | {col_label.ljust(col_w)} |"
    sep = f"+-{'-'*row_w}-+-{'-'*col_w}-+"

    print(PINK + top + RESET)
    print(PINK + hdr + RESET)
    print(PINK + sep + RESET)
    for r, v in zip(row_labels, values):
        line = f"| {r.ljust(row_w)} | {str(v).ljust(col_w)} |"
        print(PINK + line + RESET)
    print(PINK + top + RESET)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to the original repository")
    parser.add_argument("--patch", required=True, help="Path to the patch file for the repository")
    parser.add_argument("--repo_copy", required=True, help="Path to the copy repository folder to create")
    parser.add_argument("--module", default=".", help="Subfolder (module) inside repo_copy; default='.'")
    parser.add_argument("--Dtest", required=True, help="Test class for Maven: mvn clean test -Dtest=...")
    parser.add_argument("--poc_string", required=True, help="String to count from target/surefire-reports (case-insensitive substring)")
    args = parser.parse_args()

    src_repo = Path(args.repo).resolve()
    patch_path = Path(args.patch).resolve()
    repo_copy = Path(args.repo_copy).resolve()
    module_rel = Path(args.module)
    module_dir = (repo_copy / module_rel).resolve()

    print(f"[INFO] repo       = {src_repo}")
    print(f"[INFO] patch      = {patch_path}")
    print(f"[INFO] repo_copy  = {repo_copy}")
    print(f"[INFO] module     = {args.module}")
    print(f"[INFO] Dtest      = {args.Dtest}")
    print(f"[INFO] poc_string = {args.poc_string}")
    print()

    # Step 1: copy repo excluding .git
    print("[STEP 1] Copy repo (excluding .git) -> repo_copy")
    copy_repo_without_git(src_repo, repo_copy)

    # Step 2: git init + first commit
    print("[STEP 2] git init + first commit in repo_copy")
    baseline_commit = git_init_and_first_commit(repo_copy)
    print(f"[INFO] baseline commit: {baseline_commit}")
    print()

    if not module_dir.is_dir():
        raise FileNotFoundError(f"Module directory does not exist: {module_dir}")

    mvn_cmd = ["mvn", "clean", "test", f"-Dtest={args.Dtest}"]

    # Step 3: origin run
    print("[STEP 3] Run mvn tests on origin (before patch)")
    _rc1, count1 = run_mvn_and_count_from_surefire(
        label="origin_repo",
        mvn_cmd=mvn_cmd,
        module_dir=module_dir,
        poc_string=args.poc_string,
    )

    # Step 4: apply patch
    print("[STEP 4] Apply patch in repo_copy root (git apply)")
    git_apply_patch(repo_copy, patch_path)
    print("[INFO] patch applied")
    print()

    # Step 5: patched run
    patch_name = patch_path.name
    print("[STEP 5] Run mvn tests after patch")
    _rc2, count2 = run_mvn_and_count_from_surefire(
        label=patch_name,
        mvn_cmd=mvn_cmd,
        module_dir=module_dir,
        poc_string=args.poc_string,
    )

    # Step 6: pink table output
    print("[STEP 6] Result table (pink)")
    print_pink_table(
        row_labels=["origin_repo", patch_name],
        col_label=args.poc_string,
        values=[count1, count2],
    )
    print()

    # Step 7: reset to baseline
    print("[STEP 7] Reset repo_copy back to baseline commit (copy is kept)")
    git_reset_hard(repo_copy, baseline_commit)
    print("[INFO] repo_copy reset completed")
    print(f"[DONE] repo_copy kept at: {repo_copy}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed with exit code {e.returncode}: {e.cmd}")
        if e.stdout:
            print("\n--- stdout ---")
            print(e.stdout)
        if e.stderr:
            print("\n--- stderr ---")
            print(e.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        sys.exit(1)
