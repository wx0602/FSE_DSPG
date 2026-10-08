#!/usr/bin/env python3
"""Correct successes in the CVE matrix using repair failures from the RQ1 real-PoC matrix."""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from collections import Counter
from pathlib import Path


SUCCESS = "success"
REPAIR_FAILED = "repair_failed"
VALID_RESULTS = {SUCCESS, "empty", "compile_error", REPAIR_FAILED}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "When the CVE matrix says success but the RQ1 real-PoC matrix says repair_failed, "
            "set the CVE status to repair_failed"
        )
    )
    parser.add_argument(
        "--cve",
        type=Path,
        default=root / "cve_description_validation_matrix.csv",
        help="CVE matrix to correct",
    )
    parser.add_argument(
        "--rq1",
        type=Path,
        default=root / "rq1_real_poc_validation_matrix.csv",
        help="RQ1 real-PoC matrix",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show the cells that would change; do not write the file",
    )
    return parser.parse_args()


def read_matrix(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"the first column must be target_id: {path}")
        rows = list(reader)

    target_ids = [row["target_id"] for row in rows]
    if len(target_ids) != len(set(target_ids)):
        raise ValueError(f"duplicate target_id present: {path}")

    tools = reader.fieldnames[1:]
    for row in rows:
        unknown = {row[tool] for tool in tools} - VALID_RESULTS
        if unknown:
            raise ValueError(
                f"unknown status in {row['target_id']} of {path}: {sorted(unknown)}"
            )
    return list(reader.fieldnames), rows


def write_matrix_atomic(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main() -> None:
    args = parse_args()
    cve_path = args.cve.resolve()
    rq1_path = args.rq1.resolve()
    cve_header, cve_rows = read_matrix(cve_path)
    rq1_header, rq1_rows = read_matrix(rq1_path)

    if rq1_header != cve_header:
        raise ValueError(
            "column names or tool order of the two matrices differ:\n"
            f"CVE: {cve_header}\nRQ1: {rq1_header}"
        )

    tools = cve_header[1:]
    cve_by_target = {row["target_id"]: row for row in cve_rows}
    missing_targets = sorted(
        row["target_id"] for row in rq1_rows if row["target_id"] not in cve_by_target
    )
    if missing_targets:
        raise ValueError(f"target_id from RQ1 is absent from the CVE matrix: {missing_targets}")

    changes: list[tuple[str, str, str]] = []
    for rq1_row in rq1_rows:
        target_id = rq1_row["target_id"]
        cve_row = cve_by_target[target_id]
        for tool in tools:
            # Only a real-PoC repair_failed overrides an earlier success; "empty" in RQ1
            # means there is no verifiable patch and must not overwrite the CVE matrix status.
            if cve_row[tool] == SUCCESS and rq1_row[tool] == REPAIR_FAILED:
                cve_row[tool] = REPAIR_FAILED
                changes.append((target_id, tool, REPAIR_FAILED))

    action = "would modify" if args.dry_run else "modified"
    if not args.dry_run and changes:
        write_matrix_atomic(cve_path, cve_header, cve_rows)

    print(f"{action} {len(changes)} cells: {cve_path}")
    by_reason = Counter(reason for _, _, reason in changes)
    by_tool = Counter(tool for _, tool, _ in changes)
    if changes:
        print("By reason: " + ", ".join(f"{key}={value}" for key, value in by_reason.items()))
        print("By tool: " + ", ".join(f"{key}={by_tool[key]}" for key in tools if by_tool[key]))
        for target_id, tool, reason in changes:
            print(f"  {target_id},{tool}: success -> {reason}")


if __name__ == "__main__":
    main()
