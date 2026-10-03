#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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


DEFAULT_APPATCH_PATCH_ROOT = Path("/media/wql/办公/AVR_agent/sota/appatch/20260622_164413")
CANDIDATE_PATCH_RE = re.compile(r"^candidate_(\d+)\.patch$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize appatch patches to source Java diffs and record metadata."
    )
    parser.add_argument("--repo", default=str(DEFAULT_REPO_ROOT), help="Directory containing project repositories.")
    parser.add_argument("--patch", default=str(DEFAULT_APPATCH_PATCH_ROOT), help="Directory containing appatch output.")
    parser.add_argument(
        "--output",
        default=None,
        help="Directory for normalized patches. Defaults to ./normalized_patches_appatch_YYYYmmdd_HHMMSS.",
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
    batch_status = read_appatch_batch_summary(patch_root)
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "patch_source": "appatch",
        "repo_root": str(repo_root),
        "raw_patch_root": str(patch_root),
        "output_dir": str(output_dir),
        "dry_run": bool(args.dry_run),
        "project_count": len(projects),
        "selected_patch_count": 0,
        "missing_patch_count": 0,
        "normalized_patch_count": 0,
        "empty_after_normalize_count": 0,
        "no_appatch_validated_candidate_count": 0,
        "missing_patch_projects": [],
        "empty_after_normalize_projects": [],
        "no_appatch_validated_candidate_projects": [],
        "projects": {},
    }

    project_details: dict[str, object] = {}
    missing_patch_projects: list[str] = []
    empty_after_normalize_projects: list[str] = []
    no_appatch_validated_candidate_projects: list[str] = []

    for project_path in projects:
        project_name = project_path.name
        candidates = discover_appatch_patch_files(patch_root, project_name)
        patch_report = read_appatch_patch_report(patch_root, project_name)
        applicable_candidates = filter_applicable_candidates(candidates, patch_report)
        selection_candidates = applicable_candidates or candidates
        selected = choose_representative_patch(selection_candidates)
        status = batch_status.get(project_name, {})

        detail: dict[str, object] = {
            "repo_path": str(project_path),
            "candidate_patch_count": len(candidates),
            "appatch_validated_candidate_count": len(applicable_candidates),
            "patch_report_candidate_count": len(patch_report),
            "appatch_status": status.get("status"),
            "appatch_reason": status.get("reason"),
            "appatch_returncode": status.get("returncode"),
            "appatch_elapsed_seconds": status.get("elapsed_seconds"),
            "selected_patch": None,
            "selected_candidate": None,
            "selected_duplicate_count": 0,
            "selected_sha256": None,
            "selected_appatch_apply_check_ok": None,
            "selected_appatch_reconstruction_ok": None,
            "selected_appatch_reconstruction_error": None,
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

        if patch_report and not applicable_candidates:
            no_appatch_validated_candidate_projects.append(project_name)

        report["selected_patch_count"] = int(report["selected_patch_count"]) + 1
        raw_text = decode_patch(selected.data)
        patch_text, extracted = extract_patch_text(raw_text)
        patch_text, rewritten_paths = rewrite_missing_paths_by_suffix(patch_text, project_path)
        analysis = analyze_patch(patch_text)
        normalized_path = output_dir / f"{project_name}.patch"
        has_normalized_content = bool(analysis.normalized_text.strip())
        selected_report = patch_report_entry_for_path(patch_report, selected.path)

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
                "selected_candidate": candidate_number(selected.path),
                "selected_duplicate_count": selected.duplicate_count,
                "selected_sha256": selected.sha256,
                "selected_appatch_apply_check_ok": report_apply_check_ok(selected_report),
                "selected_appatch_reconstruction_ok": report_reconstruction_ok(selected_report),
                "selected_appatch_reconstruction_error": compact_text(report_reconstruction_error(selected_report)),
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
    report["no_appatch_validated_candidate_count"] = len(no_appatch_validated_candidate_projects)
    report["no_appatch_validated_candidate_projects"] = no_appatch_validated_candidate_projects
    report["projects"] = project_details

    if not args.dry_run:
        write_json(output_dir / NORMALIZE_REPORT, report)

    print_summary(report, wrote_report=not args.dry_run)
    return 0


def discover_appatch_patch_files(patch_root: Path, project_name: str) -> list[Path]:
    project_dir = patch_root / project_name
    if not project_dir.is_dir():
        return []
    return sorted(project_dir.glob("candidate_*.patch"), key=candidate_sort_key)


def read_appatch_patch_report(patch_root: Path, project_name: str) -> list[dict[str, object]]:
    report_path = patch_root / project_name / "patch_report.json"
    if not report_path.is_file():
        return []
    try:
        value = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def filter_applicable_candidates(
    candidates: list[Path], patch_report: list[dict[str, object]]
) -> list[Path]:
    """Keep candidates that Appatch successfully reconstructed and apply-checked.

    Older Appatch outputs may not contain a patch report. Preserve the previous
    representative-selection behavior for those outputs because there is no
    validation metadata to use.
    """
    if not patch_report:
        return candidates

    applicable: list[Path] = []
    for candidate in candidates:
        entry = patch_report_entry_for_path(patch_report, candidate)
        if report_reconstruction_ok(entry) is True and report_apply_check_ok(entry) is True:
            applicable.append(candidate)
    return applicable


def read_appatch_batch_summary(patch_root: Path) -> dict[str, dict[str, object]]:
    summary_path = patch_root / "batch_summary.json"
    if not summary_path.is_file():
        return {}
    try:
        value = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        return {}

    status_by_project: dict[str, dict[str, object]] = {}
    for item in value["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("project"), str):
            continue
        status_by_project[item["project"]] = {
            "status": item.get("status"),
            "reason": item.get("reason"),
            "returncode": item.get("returncode"),
            "elapsed_seconds": item.get("elapsed_seconds"),
            "auto_selected_repo": item.get("auto_selected_repo"),
            "output": item.get("output"),
        }
    return status_by_project


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


def patch_report_entry_for_path(patch_report: list[dict[str, object]], path: Path) -> dict[str, object]:
    selected_name = path.name
    selected_candidate = candidate_number(path)
    for item in patch_report:
        patch_file = item.get("patch_file")
        if isinstance(patch_file, str) and patch_file == selected_name:
            return item
        candidate = item.get("candidate")
        if isinstance(candidate, int) and selected_candidate == candidate:
            return item
    return {}


def report_apply_check_ok(entry: dict[str, object]) -> bool | None:
    apply_check = entry.get("apply_check")
    if not isinstance(apply_check, dict):
        return None
    ok = apply_check.get("ok")
    return ok if isinstance(ok, bool) else None


def report_reconstruction_ok(entry: dict[str, object]) -> bool | None:
    reconstruction = entry.get("reconstruction")
    if not isinstance(reconstruction, dict):
        return None
    ok = reconstruction.get("ok")
    return ok if isinstance(ok, bool) else None


def report_reconstruction_error(entry: dict[str, object]) -> str | None:
    reconstruction = entry.get("reconstruction")
    if not isinstance(reconstruction, dict):
        return None
    error = reconstruction.get("error")
    return error if isinstance(error, str) else None


def candidate_number(path: Path) -> int | None:
    match = CANDIDATE_PATCH_RE.match(path.name)
    return int(match.group(1)) if match else None


def candidate_sort_key(path: Path) -> tuple[int, str]:
    number = candidate_number(path)
    return number if number is not None else 10**9, path.name


def compact_text(value: str | None, limit: int = 500) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value[-limit:] if len(value) > limit else value


def default_output_dir() -> Path:
    from time import strftime

    return Path.cwd() / f"normalized_patches_appatch_{strftime('%Y%m%d_%H%M%S')}"


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
    print(
        "no Appatch-validated candidate count: "
        f"{report['no_appatch_validated_candidate_count']}"
    )

    if wrote_report:
        print(f"report: {Path(str(report['output_dir'])) / NORMALIZE_REPORT}")


if __name__ == "__main__":
    raise SystemExit(main())
