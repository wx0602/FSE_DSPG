#!/usr/bin/env python3
"""Export the PoC-merged successful-patch lists for the first five experiment groups."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MERGED_ROOT = ROOT / "poc_merged"
OUTPUT_ROOT = ROOT / "first_five_successful_patch_lists"

EXPERIMENTS = (
    ("cve_description_validation_matrix.csv", "1_cve_description_only"),
    ("with_upstream_patch_matrix.csv", "2_with_upstream_patch"),
    ("with_vuln_chain_validation_matrix.csv", "3_with_vuln_chain"),
    ("with_selfgen_upstream_patch_matrix.csv", "4_with_selfgen_upstream_patch"),
    (
        "with_selfgen_upstream_patch_and_vuln_chain_matrix.csv",
        "5_selfgen_upstream_patch_plus_vuln_chain",
    ),
)

CRITERIA = (
    ("all_pocs_pass", "all_pocs_pass_AND_successful_patch_list.txt"),
    (
        "at_least_one_poc_pass_partial_success",
        "at_least_one_poc_pass_OR_successful_patch_list.txt",
    ),
)


def read_success_patches(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"the first CSV column must be target_id: {path}")
        tools = list(reader.fieldnames[1:])
        rows = list(reader)

    if len(rows) != 63 or len(tools) != 9:
        raise ValueError(f"matrix is not 63x9: {path}")

    patches = [
        f"{tool}__{row['target_id']}.patch"
        for tool in tools
        for row in rows
        if row[tool] == "success"
    ]
    return sorted(patches)


def main() -> None:
    for matrix_name, experiment_folder in EXPERIMENTS:
        output_dir = OUTPUT_ROOT / experiment_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        for criterion_folder, output_name in CRITERIA:
            source = MERGED_ROOT / criterion_folder / matrix_name
            patches = read_success_patches(source)
            output = output_dir / output_name
            output.write_text("\n".join(patches) + "\n", encoding="utf-8")
            print(f"{experiment_folder}/{output_name}: {len(patches)}")


if __name__ == "__main__":
    main()
