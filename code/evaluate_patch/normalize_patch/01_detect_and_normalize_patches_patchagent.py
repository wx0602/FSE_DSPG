#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from patch_workflow_common import (
    DEFAULT_REPO_ROOT,
    NORMALIZE_REPORT,
    analyze_patch,
    choose_representative_patch,
    decode_patch,
    list_projects,
    write_json,
)


DEFAULT_PATCHAGENT_PATCH_ROOT = Path(
    "/media/wql/办公/AVR_agent/sota/patchagent/PatchAgent/20260622_194449"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize PatchAgent patches to source Java diffs and record metadata."
    )
    parser.add_argument("--repo", default=str(DEFAULT_REPO_ROOT), help="Directory containing project repositories.")
    parser.add_argument(
        "--patch",
        default=str(DEFAULT_PATCHAGENT_PATCH_ROOT),
        help="Directory containing PatchAgent output.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Directory for normalized patches. Defaults to ./normalized_patches_patchagent_YYYYmmdd_HHMMSS.",
    )
    parser.add_argument("--write-empty", action="store_true", help="Write empty .patch files after filtering.")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only; do not write normalized patches.")
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
    patch_root = Path(args.patch).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve() if args.output else default_output_dir().resolve()

    projects = list_projects(repo_root, excluded_project_names(args))
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "patch_source": "patchagent",
        "repo_root": str(repo_root),
        "raw_patch_root": str(patch_root),
        "output_dir": str(output_dir),
        "dry_run": bool(args.dry_run),
        "project_count": len(projects),
        "selected_patch_count": 0,
        "missing_patch_count": 0,
        "normalized_patch_count": 0,
        "empty_after_normalize_count": 0,
        "missing_patch_projects": [],
        "empty_after_normalize_projects": [],
        "projects": {},
    }

    project_details: dict[str, object] = {}
    missing_patch_projects: list[str] = []
    empty_after_normalize_projects: list[str] = []

    for project_path in projects:
        project_name = project_path.name
        candidates = discover_patchagent_patch_files(patch_root, project_name)
        selected = choose_representative_patch(candidates)
        status = read_patchagent_status(patch_root, project_name)

        detail: dict[str, object] = {
            "repo_path": str(project_path),
            "candidate_patch_count": len(candidates),
            "patchagent_status": status.get("status") if status else None,
            "patchagent_returncode": status.get("returncode") if status else None,
            "patchagent_duration_sec": status.get("duration_sec") if status else None,
            "patchagent_repo_resolution": status.get("repo_resolution") if status else None,
            "patchagent_patch_exists": status.get("patch_exists") if status else None,
            "patchagent_patch_size": status.get("patch_size") if status else None,
            "patchagent_patch_kind": status.get("patch_kind") if status else None,
            "selected_patch": None,
            "selected_duplicate_count": 0,
            "selected_sha256": None,
            "modifies_pom_xml": False,
            "pom_paths": [],
            "java_diff_count": 0,
            "kept_java_diff_count": 0,
            "normalized_patch": None,
            "empty_after_normalize": False,
            "diff_extracted_from_wrapper": False,
            "rewritten_paths": {},
        }

        if selected is None:
            missing_patch_projects.append(project_name)
            project_details[project_name] = detail
            continue

        report["selected_patch_count"] = int(report["selected_patch_count"]) + 1
        raw_text = decode_patch(selected.data)
        patch_text, extracted = extract_patch_text(raw_text)
        patch_text, rewritten_paths = rewrite_missing_paths_by_suffix(patch_text, project_path)
        analysis = analyze_patch(patch_text)
        normalized_path = output_dir / f"{project_name}.patch"
        has_normalized_content = bool(analysis.normalized_text.strip())

        if has_normalized_content or args.write_empty:
            if not args.dry_run:
                normalized_path.write_text(analysis.normalized_text, encoding="utf-8")
            if has_normalized_content:
                report["normalized_patch_count"] = int(report["normalized_patch_count"]) + 1
            detail["normalized_patch"] = str(normalized_path)

        if not has_normalized_content:
            report["empty_after_normalize_count"] = int(report["empty_after_normalize_count"]) + 1
            empty_after_normalize_projects.append(project_name)
            detail["empty_after_normalize"] = True

        detail.update(
            {
                "selected_patch": str(selected.path),
                "selected_duplicate_count": selected.duplicate_count,
                "selected_sha256": selected.sha256,
                "modifies_pom_xml": bool(analysis.pom_paths),
                "pom_paths": analysis.pom_paths,
                "java_diff_count": analysis.java_diff_count,
                "kept_java_diff_count": analysis.kept_java_diff_count,
                "diff_extracted_from_wrapper": extracted,
                "rewritten_paths": rewritten_paths,
            }
        )
        project_details[project_name] = detail

    report["missing_patch_count"] = len(missing_patch_projects)
    report["missing_patch_projects"] = missing_patch_projects
    report["empty_after_normalize_projects"] = empty_after_normalize_projects
    report["projects"] = project_details

    if not args.dry_run:
        write_json(output_dir / NORMALIZE_REPORT, report)

    print_summary(report, wrote_report=not args.dry_run)
    return 0


def discover_patchagent_patch_files(patch_root: Path, project_name: str) -> list[Path]:
    project_dir = patch_root / project_name
    if not project_dir.is_dir():
        return []

    candidates: list[Path] = []
    status = read_patchagent_status(patch_root, project_name)
    patch_value = status.get("patch") if status else None
    if isinstance(patch_value, str):
        status_patch = Path(patch_value)
        if not status_patch.is_absolute():
            status_patch = project_dir / status_patch
        if status_patch.is_file() and status_patch.parent.resolve() == project_dir.resolve():
            candidates.append(status_patch)

    default_patch = project_dir / "patch.diff"
    if default_patch.is_file():
        candidates.append(default_patch)

    candidates.extend(sorted(project_dir.glob("*.diff"), key=lambda item: item.name))
    candidates.extend(sorted(project_dir.glob("*.patch"), key=lambda item: item.name))
    return unique_paths(candidates)


def read_patchagent_status(patch_root: Path, project_name: str) -> dict[str, object]:
    status_path = patch_root / project_name / "status.json"
    if not status_path.is_file():
        return {}
    try:
        value = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(path)
    return result


def extract_patch_text(text: str) -> tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("diff --git ") or line.startswith("--- "):
            return "".join(lines[index:]), index > 0
    return text, False


def rewrite_missing_paths_by_suffix(text: str, repo_path: Path) -> tuple[str, dict[str, str]]:
    lines = text.splitlines(keepends=True)
    rewrites: dict[str, str] = {}
    output: list[str] = []

    for line in lines:
        output.append(rewrite_path_line(line, repo_path, rewrites))

    return "".join(output), rewrites


def rewrite_path_line(line: str, repo_path: Path, rewrites: dict[str, str]) -> str:
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line

    if body.startswith("diff --git "):
        parts = body.split()
        if len(parts) >= 4:
            old_path = strip_ab_prefix(parts[2])
            new_path = strip_ab_prefix(parts[3])
            rewritten_old = resolve_patch_path(old_path, repo_path, rewrites)
            rewritten_new = resolve_patch_path(new_path, repo_path, rewrites)
            if rewritten_old != old_path or rewritten_new != new_path:
                return f"diff --git a/{rewritten_old} b/{rewritten_new}{newline}"
        return line

    for prefix in ("--- ", "+++ "):
        if body.startswith(prefix):
            raw_path, suffix = split_header_path(body[len(prefix) :])
            stripped = strip_ab_prefix(raw_path)
            rewritten = resolve_patch_path(stripped, repo_path, rewrites)
            if rewritten != stripped:
                marker = "a/" if raw_path.startswith("a/") else "b/" if raw_path.startswith("b/") else ""
                return f"{prefix}{marker}{rewritten}{suffix}{newline}"
            return line

    return line


def split_header_path(value: str) -> tuple[str, str]:
    if "\t" in value:
        path, suffix = value.split("\t", 1)
        return path, "\t" + suffix
    if " " in value:
        path, suffix = value.split(" ", 1)
        return path, " " + suffix
    return value, ""


def strip_ab_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def resolve_patch_path(path: str, repo_path: Path, rewrites: dict[str, str]) -> str:
    if not path or path == "/dev/null":
        return path
    if path in rewrites:
        return rewrites[path]
    if (repo_path / path).exists():
        return path

    matches = sorted(
        candidate.relative_to(repo_path).as_posix()
        for candidate in repo_path.rglob(Path(path).name)
        if candidate.is_file() and candidate.relative_to(repo_path).as_posix().endswith(path)
    )
    if len(matches) == 1:
        rewrites[path] = matches[0]
        return matches[0]
    return path


def default_output_dir() -> Path:
    from time import strftime

    return Path.cwd() / f"normalized_patches_patchagent_{strftime('%Y%m%d_%H%M%S')}"


def excluded_project_names(args: argparse.Namespace) -> set[str]:
    excludes = set(args.exclude_name)
    if not args.no_default_excludes:
        excludes.add("files")
    return excludes


def print_summary(report: dict[str, object], wrote_report: bool) -> None:
    print(f"repo root: {report['repo_root']}")
    print(f"raw patch root: {report['raw_patch_root']}")
    print(f"output dir: {report['output_dir']}")
    print(f"project count: {report['project_count']}")
    print(f"selected patch count: {report['selected_patch_count']}")
    print(f"missing patch count: {report['missing_patch_count']}")
    print(f"normalized patch count: {report['normalized_patch_count']}")
    print(f"empty after normalize count: {report['empty_after_normalize_count']}")

    if wrote_report:
        print(f"report: {Path(str(report['output_dir'])) / NORMALIZE_REPORT}")


if __name__ == "__main__":
    raise SystemExit(main())
