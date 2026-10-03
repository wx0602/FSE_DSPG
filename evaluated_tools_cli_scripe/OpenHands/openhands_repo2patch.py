#!/usr/bin/env python3
"""
FINAL SCRIPT: Copy local Java repository -> initialize new Git repo -> make two commits ->
apply openhands modifications -> generate patch containing ONLY .java file changes (git apply compatible).

CLI Args (follow your spec):
  --repo=       Original Java repo path (existing Git repo, read-only, do NOT modify)
  --repo_copy=  New repo path (copied directory; must NOT contain .git if exists)
  --patch=      Final exported patch file path (including filename)
  --issue=      Issue file passed to openhands (describes problem to fix)

Fixed commit messages:
  1) commit by openhands first auto
  2) commit by openhands second auto

Core workflow:
  1) Prepare target directory (create if missing; no .git if exists)
  2) Copy source repo to new directory (exclude .git)
  3) git init in new directory (ensure clean repo)
  4) First commit (all current files)
  5) Run openhands (cd to repo_copy, execute: openhands --headless -f issue_file)
  6) Second commit (all changes after modification; allow empty commit for stability)
  7) Generate patch (git diff commit1 commit2, only *.java changes) write to --patch

Robustness:
  - Path validation, permission/IO error handling
  - git/openhands command failure capture
  - Working directory guaranteed to restore in finally
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union


FIRST_COMMIT_MSG = "commit by openhands first auto"
SECOND_COMMIT_MSG = "commit by openhands second auto"


def log(msg: str) -> None:
    print(msg, flush=True)


def run_command(
    cmd: Union[List[str], str],
    cwd: Optional[Union[str, Path]] = None,
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run external command and return CompletedProcess.
    Raise RuntimeError with clear message on failure.
    """
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=check,
            capture_output=capture_output,
            text=text,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        parts = []
        if stderr.strip():
            parts.append(stderr.strip())
        if stdout.strip() and not parts:
            parts.append(stdout.strip())
        detail = "; ".join(parts) if parts else ""
        raise RuntimeError(f"Command '{cmd}' failed with exit code {exc.returncode}: {detail}")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {cmd}\n{exc}")


def ensure_copy_dir(copy_repo: Path) -> None:
    """
    Prepare destination directory:
      - Create if missing
      - If exists, must NOT contain .git
    """
    try:
        copy_repo.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to create destination directory '{copy_repo}': {exc}")

    if (copy_repo / ".git").exists():
        raise RuntimeError(
            f"Destination directory '{copy_repo}' already contains a .git directory. "
            "Please choose a fresh location or remove the .git directory."
        )


def copy_repository_excluding_git(source_repo: Path, copy_repo: Path) -> None:
    """
    Copy source_repo to copy_repo, EXCLUDE .git directory entirely.
    Note: source_repo is never modified.
    """
    if not source_repo.exists() or not source_repo.is_dir():
        raise RuntimeError(f"Source repository '{source_repo}' does not exist or is not a directory.")

    for item in source_repo.iterdir():
        if item.name == ".git":
            continue
        dst = copy_repo / item.name
        try:
            if item.is_dir():
                shutil.copytree(item, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst)
        except Exception as exc:
            raise RuntimeError(f"Failed to copy '{item}' to '{dst}': {exc}")


def init_git_repo(repo_path: Path) -> None:
    """
    Initialize clean Git repo in repo_path (git init), set local user.name/user.email
    to avoid commit failures in environments without global config.
    """
    if (repo_path / ".git").exists():
        raise RuntimeError(
            f"Directory '{repo_path}' already contains a .git directory. "
            "Refusing to reinitialise an existing repository."
        )

    log(f"Initialising new git repository in '{repo_path}'…")
    run_command(["git", "init"], cwd=repo_path)

    try:
        run_command(["git", "config", "user.name", "openhands_auto"], cwd=repo_path)
        run_command(["git", "config", "user.email", "openhands_auto@example.com"], cwd=repo_path)
    except Exception as exc:
        log(f"Warning: failed to set local git user identity: {exc}")


def git_add_and_commit(repo_path: Path, message: str) -> str:
    """
    git add -A + commit. Use --allow-empty for stable workflow.
    Return new commit hash.
    """
    log(f"Staging all files for commit: '{message}'…")
    run_command(["git", "add", "-A"], cwd=repo_path)

    log(f"Committing changes: '{message}'…")
    run_command(["git", "commit", "--allow-empty", "-m", message], cwd=repo_path)

    res = run_command(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True)
    commit_hash = (res.stdout or "").strip()
    if not commit_hash:
        raise RuntimeError("Failed to read commit hash after committing.")
    log(f"Created commit {commit_hash} with message: '{message}'")
    return commit_hash


def openhands_modify_repo(repo_path: Path, issue_path: Path) -> None:
    """
    Custom modification hook: run openhands to fix the repo.

    Requirements:
      - Save current working directory
      - Switch to repo_path
      - Execute: openhands --headless -f issue_path
      - Always return to original directory (success or failure)
    """
    if not issue_path.exists():
        raise RuntimeError(f"Issue file '{issue_path}' does not exist.")

    original_cwd = Path.cwd()
    try:
        log(f"Switching working directory to '{repo_path}' to run openhands…")
        os.chdir(repo_path)

        cmd = ["openhands", "--headless", "-f", str(issue_path)]
        log(f"Running external command: {' '.join(cmd)}")
        run_command(cmd, cwd=repo_path)
        log("openhands command completed successfully.")
    finally:
        try:
            os.chdir(original_cwd)
            log(f"Returned to original working directory '{original_cwd}'.")
        except Exception as exc:
            raise RuntimeError(f"Failed to return to original directory '{original_cwd}': {exc}")


def generate_java_patch(repo_path: Path, commit1: str, commit2: str, patch_output: Path) -> None:
    """
    Generate git diff from commit1 to commit2, ONLY include .java files, write to patch_output.
    Output can be used with git apply.
    """
    log(f"Generating diff between commits {commit1} and {commit2} for .java files…")

    diff_cmd = ["git", "diff", commit1, commit2, "--", "*.java"]
    res = run_command(diff_cmd, cwd=repo_path, capture_output=True)
    diff_text = res.stdout or ""

    try:
        patch_output.parent.mkdir(parents=True, exist_ok=True)
        patch_output.write_text(diff_text, encoding="utf-8")
        log(f"Patch file written to '{patch_output}'.")
    except Exception as exc:
        raise RuntimeError(f"Failed to write patch to '{patch_output}': {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a Java repo, init a new Git repo, commit twice around openhands, and generate a Java-only diff patch."
    )
    parser.add_argument("--repo", required=True, help="Path to the source Java repository (existing Git repo, read-only)")
    parser.add_argument("--repo_copy", required=True, help="Path to the new copied repository (must not contain .git)")
    parser.add_argument("--patch", required=True, help="Output patch file path (including filename)")
    parser.add_argument("--issue", required=True, help="Issue file path passed to openhands (-f)")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source_repo = Path(args.repo)
    copy_repo = Path(args.repo_copy)
    patch_output = Path(args.patch)
    issue_path = Path(args.issue)

    try:
        ensure_copy_dir(copy_repo)

        log(f"Copying repository from '{source_repo}' to '{copy_repo}' (excluding .git)…")
        copy_repository_excluding_git(source_repo, copy_repo)

        init_git_repo(copy_repo)

        first_commit = git_add_and_commit(copy_repo, FIRST_COMMIT_MSG)

        log(f"Invoking openhands with issue file '{issue_path}'…")
        openhands_modify_repo(copy_repo, issue_path)

        second_commit = git_add_and_commit(copy_repo, SECOND_COMMIT_MSG)

        log(f"Creating Java-only patch between commits {first_commit} and {second_commit}…")
        generate_java_patch(copy_repo, first_commit, second_commit, patch_output)

        log("Operation completed successfully.")
    except Exception as exc:
        log(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

