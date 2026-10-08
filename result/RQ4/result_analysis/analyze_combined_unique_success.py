#!/usr/bin/env python3
"""Count repair successes unique to "self-generated upstream patch + vulnerability chain" relative to the other experiments."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from build_result_matrices import build_matrix, find_latest_pipeline


MERGED_ROOT = ROOT / "poc_merged"
COMBINED = "with_selfgen_upstream_patch_and_vuln_chain_matrix.csv"
SELF_GENERATED = "with_selfgen_upstream_patch_matrix.csv"
VULNERABILITY_CHAIN = "with_vuln_chain_validation_matrix.csv"

CRITERIA = (
    ("all_pocs_pass", "all_pocs_pass_AND"),
    ("at_least_one_poc_pass_partial_success", "at_least_one_poc_pass_OR"),
)

OUTPUTS = (
    (
        ROOT / "combined_has_but_selfgen_patch_and_vuln_chain_absent_success_counts.csv",
        "self_and_chain_absent",
    ),
    (
        ROOT / "combined_has_but_vuln_chain_and_repo_absent_success_counts.csv",
        "chain_and_repository_absent",
    ),
)


def read_success_sets(path: Path) -> tuple[list[str], dict[str, set[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"the first CSV column must be target_id: {path}")
        tools = list(reader.fieldnames[1:])
        rows = list(reader)

    if len(rows) != 63 or len(tools) != 9:
        raise ValueError(f"matrix is not 63x9: {path}")
    return tools, {
        tool: {row["target_id"] for row in rows if row[tool] == "success"}
        for tool in tools
    }


def read_upstream_repository_success_sets(
) -> tuple[list[str], dict[str, set[str]]]:
    pipeline = find_latest_pipeline(WORKSPACE_ROOT / "upstream_repo_validation")
    tools, targets, matrix = build_matrix(pipeline)
    if len(targets) != 63 or len(tools) != 9:
        raise ValueError(f"upstream repository matrix is not 63x9: {pipeline}")
    return tools, {
        tool: {target for target in targets if matrix[target][tool] == "success"}
        for tool in tools
    }


def calculate() -> tuple[list[str], dict[str, dict[str, dict[str, int]]]]:
    upstream_tools, upstream = read_upstream_repository_success_sets()
    results: dict[str, dict[str, dict[str, int]]] = {
        key: {} for _, key in OUTPUTS
    }

    for criterion_folder, criterion_label in CRITERIA:
        folder = MERGED_ROOT / criterion_folder
        tools, combined = read_success_sets(folder / COMBINED)
        self_tools, self_generated = read_success_sets(folder / SELF_GENERATED)
        chain_tools, chain = read_success_sets(folder / VULNERABILITY_CHAIN)
        if tools != self_tools or tools != chain_tools or tools != upstream_tools:
            raise ValueError(f"tool columns or their order differ: {criterion_folder}")

        results["self_and_chain_absent"][criterion_label] = {
            tool: len(combined[tool] - self_generated[tool] - chain[tool])
            for tool in tools
        }
        results["chain_and_repository_absent"][criterion_label] = {
            tool: len(combined[tool] - chain[tool] - upstream[tool])
            for tool in tools
        }

    return upstream_tools, results


def main() -> None:
    tools, results = calculate()
    criterion_labels = [label for _, label in CRITERIA]
    for output, result_key in OUTPUTS:
        with output.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["tool_name", *criterion_labels])
            for tool in tools:
                writer.writerow(
                    [tool, *(results[result_key][label][tool] for label in criterion_labels)]
                )
        print(f"Generated: {output}")


if __name__ == "__main__":
    main()
