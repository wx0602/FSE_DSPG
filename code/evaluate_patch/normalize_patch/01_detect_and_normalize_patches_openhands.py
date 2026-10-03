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


DEFAULT_OPENHANDS_PATCH_ROOT = Path(
    "/media/wql/办公/AVR_agent/sota/openhands/batch_runs/run_20260607_234533"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize OpenHands patches to source Java diffs and record metadata."
    )
    parser.add_argument("--repo", default=str(DEFAULT_REPO_ROOT), help="Directory containing project repositories.")
    parser.add_argument(
        "--patch",
        default=str(DEFAULT_OPENHANDS_PATCH_ROOT),
        help="Directory containing OpenHands output.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Directory for normalized patches. Defaults to ./normalized_patches_openhands_YYYYmmdd_HHMMSS.",
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
    patch_root = resolve_patch_root(Path(args.patch).expanduser()).resolve()
    output_dir = Path(args.output).expanduser().resolve() if args.output else default_output_dir().resolve()

    projects = list_projects(repo_root, excluded_project_names(args))
    summary = read_openhands_summary(patch_root)
    summary_results = openhands_results_by_project(summary)
    summary_counts = summary.get("counts") if isinstance(summary.get("counts"), dict) else {}

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "patch_source": "openhands",
        "repo_root": str(repo_root),
        "raw_patch_root": str(patch_root),
        "output_dir": str(output_dir),
        "dry_run": bool(args.dry_run),
        "openhands_generated_at": summary.get("generated_at"),
        "openhands_counts": summary_counts,
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
        candidates = discover_openhands_patch_files(patch_root, project_name, summary_results.get(project_name, {}))
        selected = choose_representative_patch(candidates)
        status = summary_results.get(project_name, {})

        detail: dict[str, object] = {
            "repo_path": str(project_path),
            "candidate_patch_count": len(candidates),
            "openhands_status": status.get("status") if status else None,
            "openhands_exit_code": status.get("exit_code") if status else None,
            "openhands_elapsed_seconds": status.get("elapsed_seconds") if status else None,
            "openhands_repo": status.get("repo") if status else None,
            "openhands_repo_copy": status.get("repo_copy") if status else None,
            "openhands_patch": status.get("patch") if status else None,
            "openhands_log": status.get("log") if status else None,
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


def resolve_patch_root(path: Path) -> Path:
    if path.exists():
        return path
    parent = path.parent
    if not parent.is_dir():
        return path
    matches = sorted(item for item in parent.iterdir() if item.is_dir() and item.name.startswith(path.name))
    if len(matches) == 1:
        return matches[0]
    return path


def discover_openhands_patch_files(
    patch_root: Path, project_name: str, status: dict[str, object]
) -> list[Path]:
    if not patch_root.exists():
        raise FileNotFoundError(f"patch root does not exist: {patch_root}")

    candidates: list[Path] = []
    patch_value = status.get("patch") if status else None
    if isinstance(patch_value, str):
        status_patch = Path(patch_value)
        if status_patch.is_file():
            candidates.append(status_patch)
        else:
            candidates.extend(paths_matching_project(patch_root, status_patch.name, project_name))

    candidates.extend(paths_matching_project(patch_root, f"{project_name}.patch", project_name))
    candidates.extend(paths_matching_project(patch_root, f"{project_name}.diff", project_name))
    return unique_paths(candidates)


def paths_matching_project(patch_root: Path, filename: str, project_name: str) -> list[Path]:
    candidates: list[Path] = []
    for base in (patch_root, patch_root / "patches"):
        candidate = base / filename
        if candidate.is_file():
            candidates.append(candidate)

    for base in (patch_root, patch_root / "patches"):
        if not base.is_dir():
            continue
        candidates.extend(sorted(base.glob(f"{project_name}*.patch"), key=lambda item: item.name))
        candidates.extend(sorted(base.glob(f"{project_name}*.diff"), key=lambda item: item.name))

    return candidates


def read_openhands_summary(patch_root: Path) -> dict[str, object]:
    summary_path = patch_root / "summary.json"
    if not summary_path.is_file():
        return {}
    try:
        value = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def openhands_results_by_project(summary: dict[str, object]) -> dict[str, dict[str, object]]:
    raw_results = summary.get("results")
    if not isinstance(raw_results, list):
        return {}

    results: dict[str, dict[str, object]] = {}
    for item in raw_results:
        if not isinstance(item, dict) or not isinstance(item.get("project"), str):
            continue
        results[item["project"]] = item
    return results


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
    path_index_holder: list[dict[str, list[str]] | None] = [None]
    output: list[str] = []
    previous_old_path_was_dev_null = False

    for line in lines:
        skip_missing_resolution = line.startswith("+++ ") and previous_old_path_was_dev_null
        output.append(rewrite_path_line(line, repo_path, rewrites, path_index_holder, skip_missing_resolution))
        previous_old_path_was_dev_null = line_old_path_is_dev_null(line)

    return "".join(output), rewrites


def rewrite_path_line(
    line: str,
    repo_path: Path,
    rewrites: dict[str, str],
    path_index_holder: list[dict[str, list[str]] | None],
    skip_missing_resolution: bool,
) -> str:
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line

    if body.startswith("diff --git "):
        parts = body.split()
        if len(parts) >= 4:
            old_raw = parts[2]
            new_raw = parts[3]
            old_path = strip_ab_prefix(old_raw)
            new_path = strip_ab_prefix(new_raw)
            old_rewritten = resolve_patch_path_with_known_prefix(old_path, repo_path, rewrites, path_index_holder)
            new_rewritten = resolve_patch_path_with_known_prefix(new_path, repo_path, rewrites, path_index_holder)
            if old_rewritten != old_path or new_rewritten != new_path:
                return f"diff --git a/{old_rewritten} b/{new_rewritten}{newline}"
        return line

    for prefix in ("--- ", "+++ "):
        if body.startswith(prefix):
            raw_path, suffix = split_header_path(body[len(prefix) :])
            stripped = strip_ab_prefix(raw_path)
            if skip_missing_resolution and not (repo_path / stripped).exists():
                rewritten = resolve_by_known_prefix(stripped, repo_path, rewrites)
                if rewritten == stripped:
                    return line
            else:
                rewritten = resolve_patch_path_with_known_prefix(stripped, repo_path, rewrites, path_index_holder)
            if rewritten != stripped:
                marker = "a/" if raw_path.startswith("a/") else "b/" if raw_path.startswith("b/") else ""
                return f"{prefix}{marker}{rewritten}{suffix}{newline}"
            return line

    return line


def resolve_patch_path_with_known_prefix(
    path: str, repo_path: Path, rewrites: dict[str, str], path_index_holder: list[dict[str, list[str]] | None]
) -> str:
    prefixed = resolve_by_known_prefix(path, repo_path, rewrites)
    if prefixed != path:
        return prefixed
    return resolve_patch_path(path, repo_path, rewrites, path_index_holder)


def resolve_by_known_prefix(path: str, repo_path: Path, rewrites: dict[str, str]) -> str:
    if not path or path == "/dev/null":
        return path
    for old, new in sorted(rewrites.items(), key=lambda item: len(item[0]), reverse=True):
        if not new.endswith(old):
            continue
        prefix = new[: -len(old)]
        candidate = f"{prefix}{path}"
        if candidate != path and (repo_path / candidate).parent.exists():
            rewrites[path] = candidate
            return candidate
    return path


def line_old_path_is_dev_null(line: str) -> bool:
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line
    if not body.startswith("--- "):
        return False
    raw_path, _suffix = split_header_path(body[len("--- ") :])
    return strip_ab_prefix(raw_path) == "/dev/null"


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


def resolve_patch_path(
    path: str, repo_path: Path, rewrites: dict[str, str], path_index_holder: list[dict[str, list[str]] | None]
) -> str:
    if not path or path == "/dev/null":
        return path
    if path in rewrites:
        return rewrites[path]
    if (repo_path / path).exists():
        return path

    if path_index_holder[0] is None:
        path_index_holder[0] = build_path_index(repo_path)

    path_index = path_index_holder[0]
    matches = sorted(
        candidate for candidate in path_index.get(Path(path).name, []) if candidate.endswith(path)
    )
    if len(matches) == 1:
        rewrites[path] = matches[0]
        return matches[0]
    return path


def build_path_index(repo_path: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for candidate in repo_path.rglob("*"):
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(repo_path).as_posix()
        index.setdefault(candidate.name, []).append(relative_path)
    return index


def default_output_dir() -> Path:
    from time import strftime

    return Path.cwd() / f"normalized_patches_openhands_{strftime('%Y%m%d_%H%M%S')}"


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
