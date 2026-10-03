#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from patch_workflow_common import (
    DEFAULT_RAW_PATCH_ROOT,
    DEFAULT_REPO_ROOT,
    NORMALIZE_REPORT,
    analyze_patch,
    choose_representative_patch,
    decode_patch,
    discover_patch_files,
    list_projects,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize SWE-agent patches to source Java diffs and record metadata."
    )
    parser.add_argument("--repo", default=str(DEFAULT_REPO_ROOT), help="Directory containing project repositories.")
    parser.add_argument("--patch", default=str(DEFAULT_RAW_PATCH_ROOT), help="Directory containing raw patches.")
    parser.add_argument(
        "--output",
        default=None,
        help="Directory for normalized patches. Defaults to ./normalized_patches_sweagent_YYYYmmdd_HHMMSS.",
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
        "patch_source": "sweagent",
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
        candidates = discover_patch_files(patch_root, project_name)
        selected = choose_representative_patch(candidates)

        detail: dict[str, object] = {
            "repo_path": str(project_path),
            "candidate_patch_count": len(candidates),
            "selected_patch": None,
            "selected_duplicate_count": 0,
            "selected_sha256": None,
            "modifies_pom_xml": False,
            "pom_paths": [],
            "java_diff_count": 0,
            "kept_java_diff_count": 0,
            "normalized_patch": None,
            "empty_after_normalize": False,
        }

        if selected is None:
            missing_patch_projects.append(project_name)
            project_details[project_name] = detail
            continue

        report["selected_patch_count"] = int(report["selected_patch_count"]) + 1
        analysis = analyze_patch(decode_patch(selected.data))
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


def default_output_dir() -> Path:
    from time import strftime

    return Path.cwd() / f"normalized_patches_sweagent_{strftime('%Y%m%d_%H%M%S')}"


def excluded_project_names(args: argparse.Namespace) -> set[str]:
    excludes = set(args.exclude_name)
    if not args.no_default_excludes:
        excludes.add("files")
    return excludes


if __name__ == "__main__":
    raise SystemExit(main())
