#!/usr/bin/env python3
"""Export completed Codex patches into the DSPG-Bench result layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path


MAPPINGS = {
    "issue_only_CVE_discribtions": "RQ1/baseline",
    "issue_with_poc": "RQ1/with_downstream_poc",
    "issue_with_chains": "RQ2/with_vpp",
    "issue_with_upstream_repo": "RQ3/with_upstream_repository",
    "issue_with_upstream_patches": "RQ3/with_gt_upstream_patch",
    "issue_with_upresult": "RQ3/bootstrapped_repair",
    "issue_with_all": "RQ4/combined_strategy",
}

DIFF_PATH_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)


def read_status(path: Path) -> dict[str, object]:
    fields = path.read_text(encoding="utf-8").rstrip("\n").split("\t")
    if len(fields) != 8:
        raise ValueError(f"unexpected status format: {path}")
    return {
        "task": fields[0],
        "status": fields[1],
        "codex_exit": int(fields[2]),
        "patch_bytes": int(fields[3]),
        "started_at": fields[4],
        "finished_at": fields[5],
        "model": fields[6],
        "reasoning_effort": fields[7],
    }


def validate_patch(task: str, patch_text: str) -> list[str]:
    if not patch_text.strip():
        raise ValueError(f"empty patch for {task}")
    paths = [left for left, right in DIFF_PATH_RE.findall(patch_text) if left == right]
    if not paths:
        raise ValueError(f"no same-path unified diffs in patch for {task}")
    for path in paths:
        lowered = path.lower()
        parts = lowered.split("/")
        if parts[-1] == "pom.xml" or "test" in parts or "tests" in parts or not lowered.endswith(".java"):
            raise ValueError(f"non-production-Java path in {task}: {path}")
    return paths


def export_experiment(raw_root: Path, target_root: Path, experiment: str, force: bool) -> None:
    source = raw_root / experiment
    destination = target_root / "result" / MAPPINGS[experiment] / "codex"
    status_files = sorted((source / "status").glob("*.tsv"))
    if len(status_files) != 63:
        raise ValueError(f"{experiment}: expected 63 statuses, found {len(status_files)}")
    if destination.exists():
        if not force:
            raise FileExistsError(f"destination already exists: {destination}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    projects: dict[str, object] = {}
    models: Counter[str] = Counter()
    for status_file in status_files:
        status = read_status(status_file)
        task = str(status["task"])
        if status["codex_exit"] != 0 or status["status"] != "patched":
            raise ValueError(f"{experiment}/{task}: unsuccessful status {status}")

        source_patch = source / "patches" / task / "patch.diff"
        patch_bytes = source_patch.read_bytes()
        patch_text = patch_bytes.decode("utf-8")
        diff_paths = validate_patch(task, patch_text)
        if len(patch_bytes) != status["patch_bytes"]:
            raise ValueError(f"{experiment}/{task}: status byte count does not match patch")

        output_patch = destination / f"{task}.patch"
        output_patch.write_bytes(patch_bytes)
        model_key = f"{status['model']}/{status['reasoning_effort']}"
        models[model_key] += 1
        projects[task] = {
            "source_status": status["status"],
            "codex_exit": status["codex_exit"],
            "patch_bytes": status["patch_bytes"],
            "model": status["model"],
            "reasoning_effort": status["reasoning_effort"],
            "started_at": status["started_at"],
            "finished_at": status["finished_at"],
            "sha256": hashlib.sha256(patch_bytes).hexdigest(),
            "diff_paths": diff_paths,
            "normalized_patch": f"{task}.patch",
            "empty_after_normalize": False,
        }

    report = {
        "patch_source": "codex",
        "source_experiment": experiment,
        "paper_setting": MAPPINGS[experiment],
        "project_count": 63,
        "selected_patch_count": 63,
        "missing_patch_count": 0,
        "normalized_patch_count": 63,
        "empty_after_normalize_count": 0,
        "pom_projects": [],
        "test_projects": [],
        "missing_patch_projects": [],
        "empty_after_normalize_projects": [],
        "model_reasoning_counts": dict(sorted(models.items())),
        "normalization": "Runner-exported production Java diffs; pom.xml and test paths excluded.",
        "projects": projects,
    }
    (destination / "normalize_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"{experiment} -> {destination}: 63 patches + normalize_report.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=Path(__file__).resolve().parent / "results")
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--experiments",
        nargs="+",
        choices=tuple(MAPPINGS),
        default=list(MAPPINGS),
        help="Experiments to export (default: all).",
    )
    args = parser.parse_args()

    raw_root = args.raw_root.expanduser().resolve()
    target_root = args.target_root.expanduser().resolve()
    if not (target_root / ".git").is_dir():
        raise ValueError(f"target is not a Git repository: {target_root}")
    for experiment in args.experiments:
        export_experiment(raw_root, target_root, experiment, args.force)


if __name__ == "__main__":
    main()
