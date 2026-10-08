#!/usr/bin/env python3
"""Generate a status-matrix CSV of target_id × tool from each group's patch validation results.

RQ1 real-PoC validation takes priority over the CVE-description experiment: a cell the
CVE-description experiment first judged as success but that fails RQ1 real-PoC validation is recorded as repair_failed.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENTS = (
    "cve_description_validation",
    "vuln_chain_validation",
    "with_upstream_patch_results",
    "with_selfgen_upstream_patch_results",
    "selfgen_upstream_patch_and_vuln_chain_validation",
    "with_poc_validation_results",
)
RQ1_MATRIX = "rq1_real_poc_validation_matrix.csv"

SUCCESS = "success"
EMPTY = "empty"
COMPILE_ERROR = "compile_error"
REPAIR_FAILED = "repair_failed"
VALID_RESULTS = {SUCCESS, EMPTY, COMPILE_ERROR, REPAIR_FAILED}

TOOL_DIR_RE = re.compile(
    r"^normalized_patches_(?P<tool>.+?)_\d{8}_\d{6}$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a target_id × tool repair-result matrix for each experiment group"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Root directory holding each experiment's results folder (default: the script's directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="CSV output directory (default: root)",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_latest_pipeline(experiment_dir: Path) -> Path:
    """Select the newest complete validation batch by directory-name timestamp."""
    candidates = sorted(
        experiment_dir.glob("nine_patch_validation_*/pipeline_summary.json"),
        key=lambda path: path.parent.name,
    )
    if not candidates:
        raise FileNotFoundError(
            f"no nine_patch_validation_*/pipeline_summary.json under {experiment_dir}"
        )

    # Some experiments were re-run; only batches containing every patched summary are usable.
    complete = []
    for pipeline_path in candidates:
        pipeline = load_json(pipeline_path)
        patch_runs = pipeline.get("patch_runs", [])
        if patch_runs and all(
            patched_summary_path(pipeline_path, run).is_file() for run in patch_runs
        ):
            complete.append(pipeline_path)
    if not complete:
        raise RuntimeError(f"no complete validation batch under {experiment_dir}")
    return complete[-1]


def patched_summary_path(pipeline_path: Path, patch_run: dict[str, Any]) -> Path:
    run_dir = (
        f"{int(patch_run['run_number']):02d}_{patch_run['patch_directory']}"
    )
    return pipeline_path.parent / run_dir / "patched" / "summary.json"


def baseline_summary_path(pipeline_path: Path, patch_run: dict[str, Any]) -> Path:
    """Locate via the baseline directory name recorded in the pipeline, so absolute paths stay valid after the results directory moves."""
    configured = Path(patch_run["baseline_summary"])
    return pipeline_path.parent / configured.parent.name / "summary.json"


def extract_tool(patch_directory: str) -> str:
    match = TOOL_DIR_RE.match(patch_directory)
    if not match:
        raise ValueError(f"cannot extract the tool name from the patch directory name: {patch_directory}")
    return match.group("tool")


def index_summary(summary: dict[str, Any], source: Path) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    details = summary.get("details")
    if not isinstance(details, dict):
        raise ValueError(f"summary has no details object: {source}")

    for status, items in details.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("target_id"):
                continue
            target_id = str(item["target_id"])
            if target_id in indexed:
                raise ValueError(f"duplicate target_id in summary: {target_id} ({source})")
            indexed[target_id] = {**item, "_status": status}
    return indexed


def match_count(item: dict[str, Any]) -> int | None:
    metrics = item.get("metrics")
    if not isinstance(metrics, dict):
        return None
    value = metrics.get("match_count")
    if value is None:
        return None
    return int(value)


def classify(
    baseline_item: dict[str, Any], patched_item: dict[str, Any]
) -> str:
    """Classify by priority: missing patch, then compile failure, then a drop in vulnerability occurrences."""
    patch_candidates = int(patched_item.get("patch_candidates", 0) or 0)
    if patch_candidates == 0:
        return EMPTY

    patched_status = str(patched_item.get("_status", ""))
    metrics = patched_item.get("metrics")
    compile_ok = isinstance(metrics, dict) and bool(metrics.get("compile_ok"))
    if patched_status == "COMPILE_FAILED" or not compile_ok:
        return COMPILE_ERROR

    baseline_count = match_count(baseline_item)
    patched_count = match_count(patched_item)
    if (
        baseline_count is not None
        and patched_count is not None
        and patched_count < baseline_count
    ):
        return SUCCESS

    return REPAIR_FAILED


def build_matrix(
    pipeline_path: Path,
) -> tuple[list[str], list[str], dict[str, dict[str, str]]]:
    pipeline = load_json(pipeline_path)
    patch_runs = sorted(
        pipeline.get("patch_runs", []), key=lambda run: int(run["run_number"])
    )
    if not patch_runs:
        raise ValueError(f"pipeline_summary has no patch_runs: {pipeline_path}")

    tools: list[str] = []
    matrix: dict[str, dict[str, str]] = {}
    expected_targets: set[str] | None = None

    for patch_run in patch_runs:
        tool = extract_tool(str(patch_run["patch_directory"]))
        if tool in tools:
            raise ValueError(f"duplicate tool name: {tool} ({pipeline_path})")
        tools.append(tool)

        baseline_path = baseline_summary_path(pipeline_path, patch_run)
        patched_path = patched_summary_path(pipeline_path, patch_run)
        baseline = index_summary(load_json(baseline_path), baseline_path)
        patched = index_summary(load_json(patched_path), patched_path)

        targets = set(baseline)
        if expected_targets is None:
            expected_targets = targets
        elif targets != expected_targets:
            raise ValueError(
                f"target_id sets differ across baselines: {baseline_path}"
            )

        missing_results = targets - set(patched)
        extra_results = set(patched) - targets
        if missing_results or extra_results:
            raise ValueError(
                f"baseline/patched target_id mismatch: {patched_path}; "
                f"missing={sorted(missing_results)}, extra={sorted(extra_results)}"
            )

        for target_id in targets:
            result = classify(baseline[target_id], patched[target_id])
            matrix.setdefault(target_id, {})[tool] = result

    target_ids = sorted(expected_targets or set())
    return tools, target_ids, matrix


def write_matrix(
    output_path: Path,
    tools: list[str],
    target_ids: list[str],
    matrix: dict[str, dict[str, str]],
) -> Counter[str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    # utf-8-sig lets Excel detect the encoding correctly when the file is opened directly.
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["target_id", *tools])
        for target_id in target_ids:
            row = [matrix[target_id][tool] for tool in tools]
            unknown = set(row) - VALID_RESULTS
            if unknown:
                raise AssertionError(f"unknown status encountered: {sorted(unknown)}")
            counts.update(row)
            writer.writerow([target_id, *row])
    return counts


def apply_rq1_failures(
    matrix: dict[str, dict[str, str]],
    tools: list[str],
    rq1_path: Path,
) -> list[tuple[str, str]]:
    """Override a success in the CVE-description experiment with an RQ1 real-PoC repair failure."""
    with rq1_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        expected_header = ["target_id", *tools]
        if reader.fieldnames != expected_header:
            raise ValueError(
                "RQ1 matrix column names or tool order differ:\n"
                f"expected: {expected_header}\nactual: {reader.fieldnames}"
            )
        rq1_rows = list(reader)

    changes: list[tuple[str, str]] = []
    seen_targets: set[str] = set()
    for row in rq1_rows:
        target_id = row["target_id"]
        if target_id in seen_targets:
            raise ValueError(f"duplicate target_id in the RQ1 matrix: {target_id}")
        seen_targets.add(target_id)
        if target_id not in matrix:
            raise ValueError(f"target_id from RQ1 is absent from the CVE matrix: {target_id}")

        for tool in tools:
            if row[tool] == REPAIR_FAILED and matrix[target_id][tool] == SUCCESS:
                matrix[target_id][tool] = REPAIR_FAILED
                changes.append((target_id, tool))
    return changes


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_dir = (args.output_dir or root).resolve()

    for experiment in EXPERIMENTS:
        experiment_dir = root / experiment
        pipeline_path = find_latest_pipeline(experiment_dir)
        tools, target_ids, matrix = build_matrix(pipeline_path)
        rq1_changes: list[tuple[str, str]] = []
        if experiment == "cve_description_validation":
            rq1_changes = apply_rq1_failures(matrix, tools, root / RQ1_MATRIX)
        output_path = output_dir / f"{experiment}_matrix.csv"
        counts = write_matrix(output_path, tools, target_ids, matrix)
        count_text = ", ".join(f"{key}={counts[key]}" for key in sorted(VALID_RESULTS))
        rq1_text = f", RQ1 corrections={len(rq1_changes)}" if rq1_changes else ""
        print(
            f"Generated {output_path} (batch={pipeline_path.parent.name}, "
            f"{len(target_ids)} targets × {len(tools)} tools; {count_text}"
            f"{rq1_text})"
        )


if __name__ == "__main__":
    main()
