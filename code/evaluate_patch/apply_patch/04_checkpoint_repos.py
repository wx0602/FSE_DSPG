#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from patch_workflow_common import DEFAULT_REPO_ROOT, list_projects


DEFAULT_STATE_NAME = "repo_checkpoint_state.yaml"
DEFAULT_MESSAGE = "chore: checkpoint repository state"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create or restore a YAML-recorded checkpoint for project repositories. "
            "By default this only checkpoints the inner PROJECT/repo Git repository, "
            "which is the source tree modified by validation and patch application."
        )
    )
    parser.add_argument(
        "--repo",
        default=str(DEFAULT_REPO_ROOT),
        help="Directory containing project directories, e.g. upstream_repo.",
    )
    parser.add_argument(
        "--state",
        default=None,
        help=(
            f"Unique YAML checkpoint file. Defaults to REPO_ROOT/{DEFAULT_STATE_NAME}. "
            "Use the same file for checkpoint and restore."
        ),
    )
    parser.add_argument(
        "--action",
        choices=("checkpoint", "restore", "status"),
        default="checkpoint",
        help="checkpoint records current heads; restore resets to recorded heads; status compares current heads.",
    )
    parser.add_argument(
        "--scope",
        choices=("inner", "outer", "both"),
        default="inner",
        help=(
            "Which Git repositories to checkpoint. inner means PROJECT/repo only. "
            "outer means PROJECT only. both checkpoints inner first, then outer."
        ),
    )
    parser.add_argument(
        "--message",
        default=DEFAULT_MESSAGE,
        help="Commit message used when checkpointing dirty repositories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be committed or restored without modifying repositories or writing state.",
    )
    parser.add_argument(
        "--clean-ignored",
        action="store_true",
        help="On restore, also remove ignored files with git clean -fdx instead of git clean -fd.",
    )
    parser.add_argument(
        "--exclude-name",
        action="append",
        default=[],
        help="Top-level project directory name to skip. Can be repeated.",
    )
    parser.add_argument("--no-default-excludes", action="store_true", help="Do not skip the default non-project dirs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo).expanduser().resolve()
    state_path = Path(args.state).expanduser().resolve() if args.state else repo_root / DEFAULT_STATE_NAME
    excludes = excluded_project_names(args)

    if args.action == "checkpoint":
        return checkpoint(repo_root, state_path, args, excludes)
    if args.action == "restore":
        return restore(repo_root, state_path, args)
    return status(repo_root, state_path, args)


def checkpoint(repo_root: Path, state_path: Path, args: argparse.Namespace, excludes: set[str]) -> int:
    projects = list_projects(repo_root, excludes)
    state: dict[str, Any] = {
        "version": 1,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo_root": str(repo_root),
        "scope": args.scope,
        "message": args.message,
        "dry_run": bool(args.dry_run),
        "projects": {},
    }
    counts = {
        "project_count": len(projects),
        "repo_count": 0,
        "committed": 0,
        "clean": 0,
        "missing_repo": 0,
        "not_git_repo": 0,
        "failed": 0,
        "dry_run_would_commit": 0,
    }

    for project_path in projects:
        project_record: dict[str, Any] = {"project_path": str(project_path), "repos": {}}
        for label, repo_path in repo_targets(project_path, args.scope):
            counts["repo_count"] += 1
            result = checkpoint_one_repo(repo_path, args.message, args.dry_run)
            project_record["repos"][label] = result
            increment_checkpoint_counts(counts, result)
        state["projects"][project_path.name] = project_record

    state["counts"] = counts
    if not args.dry_run:
        write_yaml(state_path, state)

    print_checkpoint_summary(repo_root, state_path, counts, wrote_state=not args.dry_run)
    return 0 if counts["failed"] == 0 else 1


def checkpoint_one_repo(repo_path: Path, message: str, dry_run: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(repo_path),
        "status": None,
        "head_before": None,
        "head_after": None,
        "dirty_before": None,
        "committed": False,
        "error": None,
    }
    if not repo_path.exists():
        result["status"] = "missing_repo"
        return result
    if not repo_path.is_dir():
        result["status"] = "missing_repo"
        result["error"] = "path exists but is not a directory"
        return result
    if not is_git_repo(repo_path):
        result["status"] = "not_git_repo"
        result["error"] = "not a Git work tree"
        return result

    head_before = git_stdout(repo_path, ["rev-parse", "HEAD"])
    dirty = has_uncommitted_changes(repo_path)
    result["head_before"] = head_before
    result["dirty_before"] = dirty

    if not dirty:
        result["status"] = "clean"
        result["head_after"] = head_before
        return result

    if dry_run:
        result["status"] = "dry_run_would_commit"
        result["head_after"] = head_before
        return result

    commit_result = commit_current_state(repo_path, message)
    if commit_result.returncode != 0:
        result["status"] = "failed"
        result["error"] = compact_process_error(commit_result)
        result["head_after"] = git_stdout(repo_path, ["rev-parse", "HEAD"])
        return result

    result["status"] = "committed"
    result["committed"] = True
    result["head_after"] = git_stdout(repo_path, ["rev-parse", "HEAD"])
    return result


def restore(repo_root: Path, state_path: Path, args: argparse.Namespace) -> int:
    state = read_yaml(state_path)
    projects = state.get("projects", {})
    if not isinstance(projects, dict):
        raise SystemExit(f"invalid checkpoint state, missing projects mapping: {state_path}")

    counts = {
        "project_count": len(projects),
        "repo_count": 0,
        "restored": 0,
        "already_at_checkpoint": 0,
        "missing_repo": 0,
        "not_git_repo": 0,
        "missing_checkpoint": 0,
        "failed": 0,
        "dry_run_would_restore": 0,
    }
    results: dict[str, Any] = {}

    for project_name, project_record in projects.items():
        repos = project_record.get("repos", {}) if isinstance(project_record, dict) else {}
        project_result: dict[str, Any] = {"repos": {}}
        for label, repo_record in repos.items():
            counts["repo_count"] += 1
            result = restore_one_repo(repo_record, args.dry_run, args.clean_ignored)
            project_result["repos"][label] = result
            increment_restore_counts(counts, result)
        results[project_name] = project_result

    print_restore_summary(repo_root, state_path, counts, dry_run=args.dry_run)
    return 0 if counts["failed"] == 0 else 1


def restore_one_repo(repo_record: dict[str, Any], dry_run: bool, clean_ignored: bool) -> dict[str, Any]:
    repo_path = Path(str(repo_record.get("path", ""))).expanduser().resolve()
    checkpoint_head = repo_record.get("head_after")
    result: dict[str, Any] = {
        "path": str(repo_path),
        "checkpoint_head": checkpoint_head,
        "head_before": None,
        "head_after": None,
        "status": None,
        "error": None,
    }
    if not checkpoint_head:
        result["status"] = "missing_checkpoint"
        result["error"] = "checkpoint record does not contain head_after"
        return result
    if not repo_path.exists():
        result["status"] = "missing_repo"
        return result
    if not is_git_repo(repo_path):
        result["status"] = "not_git_repo"
        result["error"] = "not a Git work tree"
        return result

    head_before = git_stdout(repo_path, ["rev-parse", "HEAD"])
    result["head_before"] = head_before
    if head_before == checkpoint_head and not has_uncommitted_changes(repo_path):
        result["status"] = "already_at_checkpoint"
        result["head_after"] = head_before
        return result

    if dry_run:
        result["status"] = "dry_run_would_restore"
        result["head_after"] = head_before
        return result

    reset_result = run_git(repo_path, ["reset", "--hard", str(checkpoint_head)])
    if reset_result.returncode != 0:
        result["status"] = "failed"
        result["error"] = compact_process_error(reset_result)
        return result

    clean_args = ["clean", "-fdx" if clean_ignored else "-fd"]
    clean_result = run_git(repo_path, clean_args)
    if clean_result.returncode != 0:
        result["status"] = "failed"
        result["error"] = compact_process_error(clean_result)
        return result

    result["status"] = "restored"
    result["head_after"] = git_stdout(repo_path, ["rev-parse", "HEAD"])
    return result


def status(repo_root: Path, state_path: Path, args: argparse.Namespace) -> int:
    state = read_yaml(state_path)
    projects = state.get("projects", {})
    if not isinstance(projects, dict):
        raise SystemExit(f"invalid checkpoint state, missing projects mapping: {state_path}")

    counts = {
        "project_count": len(projects),
        "repo_count": 0,
        "at_checkpoint": 0,
        "dirty_at_checkpoint": 0,
        "different_head": 0,
        "missing_repo": 0,
        "not_git_repo": 0,
        "missing_checkpoint": 0,
        "failed": 0,
    }

    for project_record in projects.values():
        repos = project_record.get("repos", {}) if isinstance(project_record, dict) else {}
        for repo_record in repos.values():
            counts["repo_count"] += 1
            result = status_one_repo(repo_record)
            key = result["status"]
            if key in counts:
                counts[key] += 1
            else:
                counts["failed"] += 1

    print_status_summary(repo_root, state_path, counts)
    return 0 if counts["failed"] == 0 else 1


def status_one_repo(repo_record: dict[str, Any]) -> dict[str, Any]:
    repo_path = Path(str(repo_record.get("path", ""))).expanduser().resolve()
    checkpoint_head = repo_record.get("head_after")
    if not checkpoint_head:
        return {"status": "missing_checkpoint"}
    if not repo_path.exists():
        return {"status": "missing_repo"}
    if not is_git_repo(repo_path):
        return {"status": "not_git_repo"}
    head = git_stdout(repo_path, ["rev-parse", "HEAD"])
    dirty = has_uncommitted_changes(repo_path)
    if head != checkpoint_head:
        return {"status": "different_head"}
    if dirty:
        return {"status": "dirty_at_checkpoint"}
    return {"status": "at_checkpoint"}


def repo_targets(project_path: Path, scope: str) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = []
    if scope in {"inner", "both"}:
        targets.append(("inner", project_path / "repo"))
    if scope in {"outer", "both"}:
        targets.append(("outer", project_path))
    return targets


def is_git_repo(repo_path: Path) -> bool:
    result = run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def has_uncommitted_changes(repo_path: Path) -> bool:
    return bool(git_stdout(repo_path, ["status", "--porcelain"]))


def commit_current_state(repo_path: Path, message: str) -> subprocess.CompletedProcess[str]:
    add_result = run_git(repo_path, ["add", "-A"])
    if add_result.returncode != 0:
        return add_result
    diff_result = run_git(repo_path, ["diff", "--cached", "--quiet"])
    if diff_result.returncode == 0:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    return run_git(repo_path, ["commit", "--no-verify", "-m", message], commit_env=True)


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


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"checkpoint state does not exist: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"invalid checkpoint state: {path}")
    return data


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def increment_checkpoint_counts(counts: dict[str, int], result: dict[str, Any]) -> None:
    status = result["status"]
    if status == "committed":
        counts["committed"] += 1
    elif status == "clean":
        counts["clean"] += 1
    elif status == "missing_repo":
        counts["missing_repo"] += 1
    elif status == "not_git_repo":
        counts["not_git_repo"] += 1
    elif status == "dry_run_would_commit":
        counts["dry_run_would_commit"] += 1
    else:
        counts["failed"] += 1


def increment_restore_counts(counts: dict[str, int], result: dict[str, Any]) -> None:
    status = result["status"]
    if status == "restored":
        counts["restored"] += 1
    elif status == "already_at_checkpoint":
        counts["already_at_checkpoint"] += 1
    elif status == "missing_repo":
        counts["missing_repo"] += 1
    elif status == "not_git_repo":
        counts["not_git_repo"] += 1
    elif status == "missing_checkpoint":
        counts["missing_checkpoint"] += 1
    elif status == "dry_run_would_restore":
        counts["dry_run_would_restore"] += 1
    else:
        counts["failed"] += 1


def print_checkpoint_summary(repo_root: Path, state_path: Path, counts: dict[str, int], wrote_state: bool) -> None:
    print(f"repo root: {repo_root}")
    print(f"checkpoint state: {state_path}")
    print(f"project count: {counts['project_count']}")
    print(f"repo count: {counts['repo_count']}")
    print(f"committed repos: {counts['committed']}")
    print(f"clean repos: {counts['clean']}")
    print(f"dry-run would commit repos: {counts['dry_run_would_commit']}")
    print(f"missing repos: {counts['missing_repo']}")
    print(f"not git repos: {counts['not_git_repo']}")
    print(f"failed repos: {counts['failed']}")
    if wrote_state:
        print(f"wrote checkpoint state: {state_path}")


def print_restore_summary(repo_root: Path, state_path: Path, counts: dict[str, int], dry_run: bool) -> None:
    print(f"repo root: {repo_root}")
    print(f"checkpoint state: {state_path}")
    print(f"project count: {counts['project_count']}")
    print(f"repo count: {counts['repo_count']}")
    print(f"restored repos: {counts['restored']}")
    print(f"already at checkpoint: {counts['already_at_checkpoint']}")
    print(f"dry-run would restore repos: {counts['dry_run_would_restore']}")
    print(f"missing checkpoint repos: {counts['missing_checkpoint']}")
    print(f"missing repos: {counts['missing_repo']}")
    print(f"not git repos: {counts['not_git_repo']}")
    print(f"failed repos: {counts['failed']}")
    if dry_run:
        print("dry-run only: no repository was modified")


def print_status_summary(repo_root: Path, state_path: Path, counts: dict[str, int]) -> None:
    print(f"repo root: {repo_root}")
    print(f"checkpoint state: {state_path}")
    print(f"project count: {counts['project_count']}")
    print(f"repo count: {counts['repo_count']}")
    print(f"at checkpoint: {counts['at_checkpoint']}")
    print(f"dirty at checkpoint: {counts['dirty_at_checkpoint']}")
    print(f"different head: {counts['different_head']}")
    print(f"missing checkpoint repos: {counts['missing_checkpoint']}")
    print(f"missing repos: {counts['missing_repo']}")
    print(f"not git repos: {counts['not_git_repo']}")
    print(f"failed repos: {counts['failed']}")


def excluded_project_names(args: argparse.Namespace) -> set[str]:
    excludes = set(args.exclude_name)
    if not args.no_default_excludes:
        excludes.add("files")
    return excludes


if __name__ == "__main__":
    raise SystemExit(main())
