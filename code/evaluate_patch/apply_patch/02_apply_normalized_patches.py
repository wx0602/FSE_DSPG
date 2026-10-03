#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path

from patch_workflow_common import APPLY_STATE, DEFAULT_REPO_ROOT, latest_normalized_dir, list_projects, write_json


BASE_APPLY_ATTEMPTS = [
    [],
    ["--recount"],
    ["--unidiff-zero"],
    ["--unidiff-zero", "--recount"],
    ["--3way"],
    ["--3way", "--recount"],
    ["--3way", "--unidiff-zero"],
    ["--3way", "--unidiff-zero", "--recount"],
]


def build_apply_attempts() -> list[list[str]]:
    attempts: list[list[str]] = []
    for strip_args in ([], ["-p0"]):
        for eof_args in ([], ["--inaccurate-eof"]):
            for base_args in BASE_APPLY_ATTEMPTS:
                attempts.append([*strip_args, *eof_args, *base_args])
    return attempts


APPLY_ATTEMPTS = build_apply_attempts()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply clean patches to vulnerable repositories.")
    parser.add_argument(
        "--repo",
        default=str(DEFAULT_REPO_ROOT),
        help="Vulnerable repository, or directory containing project repositories when --patch is a directory.",
    )
    parser.add_argument(
        "--patch",
        default=None,
        help="Clean .patch file or directory containing project.patch files. Defaults to latest ./normalized_patches_*.",
    )
    parser.add_argument(
        "--state-output",
        default=None,
        help=f"State file for rollback. Defaults to PATCH_DIR/{APPLY_STATE} or PATCH_STEM_{APPLY_STATE}.",
    )
    parser.add_argument(
        "--commit-message",
        default="chore: baseline before applying clean patch",
        help="Commit message used when a project has uncommitted changes before patch application.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Check what would be applied without modifying repos.")
    parser.add_argument(
        "--no-init-missing-git",
        action="store_true",
        help="Skip directories that are not Git repositories instead of initializing them.",
    )
    parser.add_argument(
        "--exclude-name",
        action="append",
        default=[],
        help="Top-level repo directory name to skip. Can be repeated.",
    )
    parser.add_argument("--no-default-excludes", action="store_true", help="Do not skip the default non-project dirs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo).expanduser().resolve()
    patch_input = Path(args.patch).expanduser().resolve() if args.patch else latest_normalized_dir()
    if patch_input is None:
        raise SystemExit("no --patch provided and no ./normalized_patches_* directory found")
    patch_input = patch_input.resolve()
    if not patch_input.exists():
        raise SystemExit(f"clean patch input does not exist: {patch_input}")
    if not patch_input.is_file() and not patch_input.is_dir():
        raise SystemExit(f"clean patch input is not a file or directory: {patch_input}")

    state_path = (
        Path(args.state_output).expanduser().resolve()
        if args.state_output
        else default_state_path(patch_input)
    )
    targets = build_apply_targets(repo_root, patch_input, excluded_project_names(args))
    state: dict[str, object] = {
        "version": 1,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo_root": str(repo_root),
        "patch_root": str(patch_input),
        "patch_input": str(patch_input),
        "patch_input_type": "file" if patch_input.is_file() else "directory",
        "dry_run": bool(args.dry_run),
        "projects": {},
    }

    project_results: dict[str, object] = {}
    counts: dict[str, int] = {
        "project_count": len(targets),
        "applied": 0,
        "missing_patch": 0,
        "empty_patch": 0,
        "not_git_repo": 0,
        "initialized_git_repo": 0,
        "dry_run_would_init_git_repo": 0,
        "baseline_commit_failed": 0,
        "already_applied": 0,
        "apply_failed": 0,
        "dry_run_ready": 0,
    }

    for project_name, project_path, patch_path in targets:
        result: dict[str, object] = {
            "repo_path": str(project_path),
            "patch_path": str(patch_path),
            "status": None,
            "pre_apply_head": None,
            "baseline_commit_created": False,
            "git_initialized_by_script": False,
            "baseline_head_before_commit": None,
            "apply_args": None,
            "error": None,
        }

        if not patch_path.exists():
            result["status"] = "missing_patch"
            counts["missing_patch"] += 1
            project_results[project_name] = result
            continue
        if patch_path.stat().st_size == 0 or not patch_path.read_text(encoding="utf-8", errors="replace").strip():
            result["status"] = "empty_patch"
            counts["empty_patch"] += 1
            project_results[project_name] = result
            continue

        git_repo = is_git_repo(project_path)
        pre_apply_head = None

        if not git_repo and args.no_init_missing_git:
            result["status"] = "not_git_repo"
            counts["not_git_repo"] += 1
            project_results[project_name] = result
            continue

        if git_repo:
            head_before = git_stdout(project_path, ["rev-parse", "HEAD"])
            result["baseline_head_before_commit"] = head_before
            pre_apply_head = head_before

            if patch_already_applied(project_path, patch_path):
                result["status"] = "already_applied"
                counts["already_applied"] += 1
                result["pre_apply_head"] = pre_apply_head
                project_results[project_name] = result
                continue

        if not git_repo:
            if args.dry_run:
                result["git_initialized_by_script"] = True
                result["baseline_commit_created"] = True
                counts["dry_run_would_init_git_repo"] += 1
            else:
                init_result = initialize_git_repo(project_path, args.commit_message)
                if init_result.returncode != 0:
                    result["status"] = "baseline_commit_failed"
                    result["error"] = compact_process_error(init_result)
                    counts["baseline_commit_failed"] += 1
                    project_results[project_name] = result
                    continue
                result["git_initialized_by_script"] = True
                result["baseline_commit_created"] = True
                pre_apply_head = git_stdout(project_path, ["rev-parse", "HEAD"])
                result["baseline_head_before_commit"] = pre_apply_head
                counts["initialized_git_repo"] += 1
        else:
            if has_uncommitted_changes(project_path):
                if args.dry_run:
                    result["baseline_commit_created"] = True
                else:
                    commit_result = commit_current_state(project_path, args.commit_message)
                    if commit_result.returncode != 0:
                        result["status"] = "baseline_commit_failed"
                        result["error"] = compact_process_error(commit_result)
                        counts["baseline_commit_failed"] += 1
                        project_results[project_name] = result
                        continue
                    result["baseline_commit_created"] = True
                    pre_apply_head = git_stdout(project_path, ["rev-parse", "HEAD"])

        result["pre_apply_head"] = pre_apply_head

        if args.dry_run:
            ready_args, error = first_applicable_args(project_path, patch_path)
            if ready_args is None:
                result["status"] = "apply_failed"
                result["error"] = error
                counts["apply_failed"] += 1
            else:
                result["status"] = "dry_run_ready"
                result["apply_args"] = ready_args
                counts["dry_run_ready"] += 1
            project_results[project_name] = result
            continue

        applied, apply_args, error = apply_patch(project_path, patch_path, pre_apply_head)
        if applied:
            result["status"] = "applied"
            result["apply_args"] = apply_args
            counts["applied"] += 1
        else:
            result["status"] = "apply_failed"
            result["error"] = error
            counts["apply_failed"] += 1
        project_results[project_name] = result

    state["counts"] = counts
    state["projects"] = project_results
    if not args.dry_run:
        write_json(state_path, state)

    print_summary(repo_root, patch_input, state_path, counts, wrote_state=not args.dry_run)
    return 0 if counts["apply_failed"] == 0 and counts["baseline_commit_failed"] == 0 else 1


def default_state_path(patch_input: Path) -> Path:
    if patch_input.is_dir():
        return patch_input / APPLY_STATE
    return patch_input.with_name(f"{patch_input.stem}_{APPLY_STATE}")


def build_apply_targets(repo_root: Path, patch_input: Path, exclude_names: set[str]) -> list[tuple[str, Path, Path]]:
    if patch_input.is_file():
        if not repo_root.is_dir():
            raise NotADirectoryError(f"vulnerable repo is not a directory: {repo_root}")
        return [(repo_root.name, repo_root, patch_input)]

    projects = list_projects(repo_root, exclude_names)
    return [(project_path.name, project_path, patch_input / f"{project_path.name}.patch") for project_path in projects]


def is_git_repo(repo_path: Path) -> bool:
    result = run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def has_uncommitted_changes(repo_path: Path) -> bool:
    return bool(git_stdout(repo_path, ["status", "--porcelain"]))


def initialize_git_repo(repo_path: Path, message: str) -> subprocess.CompletedProcess[str]:
    init_result = run_git(repo_path, ["init"])
    if init_result.returncode != 0:
        return init_result
    return commit_current_state(repo_path, message)


def commit_current_state(repo_path: Path, message: str) -> subprocess.CompletedProcess[str]:
    add_result = run_git(repo_path, ["add", "-A"])
    if add_result.returncode != 0:
        return add_result
    return run_git(repo_path, ["commit", "--no-verify", "-m", message], commit_env=True)


def first_applicable_args(repo_path: Path, patch_path: Path) -> tuple[list[str] | None, str | None]:
    last_error = None
    for extra_args in APPLY_ATTEMPTS:
        check_args = ["apply", "--check", "--ignore-whitespace", "--whitespace=nowarn", *extra_args, str(patch_path)]
        check_result = run_git(repo_path, check_args)
        if check_result.returncode == 0:
            return extra_args, None
        last_error = compact_process_error(check_result)
    return None, last_error


def patch_already_applied(repo_path: Path, patch_path: Path) -> bool:
    result = run_git(
        repo_path,
        ["apply", "--reverse", "--check", "--ignore-whitespace", "--whitespace=nowarn", str(patch_path)],
    )
    return result.returncode == 0


def apply_patch(repo_path: Path, patch_path: Path, pre_apply_head: str) -> tuple[bool, list[str] | None, str | None]:
    ready_args, error = first_applicable_args(repo_path, patch_path)
    if ready_args is None:
        return False, None, error

    apply_args = ["apply", "--ignore-whitespace", "--whitespace=nowarn", *ready_args, str(patch_path)]
    apply_result = run_git(repo_path, apply_args)
    if apply_result.returncode == 0:
        return True, ready_args, None

    run_git(repo_path, ["reset", "--hard", pre_apply_head])
    run_git(repo_path, ["clean", "-fd"])
    return False, ready_args, compact_process_error(apply_result)


def run_git(repo_path: Path, args: list[str], commit_env: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if commit_env:
        env.setdefault("GIT_AUTHOR_NAME", "patch-workflow")
        env.setdefault("GIT_AUTHOR_EMAIL", "patch-workflow@example.invalid")
        env.setdefault("GIT_COMMITTER_NAME", "patch-workflow")
        env.setdefault("GIT_COMMITTER_EMAIL", "patch-workflow@example.invalid")
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def git_stdout(repo_path: Path, args: list[str]) -> str:
    result = run_git(repo_path, args)
    if result.returncode != 0:
        raise RuntimeError(compact_process_error(result))
    return result.stdout.strip()


def compact_process_error(result: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return output[-4000:] if output else f"exit code {result.returncode}"


def print_summary(repo_root: Path, patch_input: Path, state_path: Path, counts: dict[str, int], wrote_state: bool) -> None:
    print(f"repo root: {repo_root}")
    print(f"clean patch input: {patch_input}")
    print(f"project count: {counts['project_count']}")
    print(f"applied patches: {counts['applied']}")
    print(f"dry-run ready patches: {counts['dry_run_ready']}")
    print(f"missing clean patches: {counts['missing_patch']}")
    print(f"empty clean patches: {counts['empty_patch']}")
    print(f"not git repos: {counts['not_git_repo']}")
    print(f"initialized git repos: {counts['initialized_git_repo']}")
    print(f"dry-run would initialize git repos: {counts['dry_run_would_init_git_repo']}")
    print(f"baseline commit failures: {counts['baseline_commit_failed']}")
    print(f"already applied patches: {counts['already_applied']}")
    print(f"apply failures: {counts['apply_failed']}")
    if wrote_state:
        print(f"rollback state: {state_path}")


def excluded_project_names(args: argparse.Namespace) -> set[str]:
    excludes = set(args.exclude_name)
    if not args.no_default_excludes:
        excludes.add("files")
    return excludes


if __name__ == "__main__":
    raise SystemExit(main())
