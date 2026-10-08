#!/usr/bin/env python3
"""Merge AI-screened CCF-A category CSV files into one table."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


INPUTS = [
    ("se", "all_ccf_a_long_papers_se_ai_screened.csv"),
    ("security", "all_ccf_a_long_papers_security_ai_screened.csv"),
    ("ai", "all_ccf_a_long_papers_ai_ai_screened.csv"),
    ("other", "all_ccf_a_long_papers_other_ai_screened.csv"),
]

OUTPUT = "all_ccf_a_long_papers_all_categories_ai_screened.csv"


def read_rows(group: str, filename: str) -> tuple[list[str], list[dict[str, str]]]:
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"missing input file: {filename}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"empty or invalid CSV header: {filename}")

        rows: list[dict[str, str]] = []
        for index, row in enumerate(reader, start=1):
            row["screen_source_group"] = group
            row["screen_source_file"] = filename
            row["screen_source_index"] = str(index)
            rows.append(row)

    return list(reader.fieldnames), rows


def main() -> None:
    fieldnames: list[str] = []
    all_rows: list[dict[str, str]] = []

    for group, filename in INPUTS:
        source_fields, rows = read_rows(group, filename)
        for field in source_fields:
            if field not in fieldnames:
                fieldnames.append(field)
        all_rows.extend(rows)

    for extra in ("screen_source_group", "screen_source_file", "screen_source_index"):
        if extra not in fieldnames:
            fieldnames.append(extra)

    with Path(OUTPUT).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    group_counts = Counter(row["screen_source_group"] for row in all_rows)
    code_counts = Counter(row.get("ai_screen_code", "") for row in all_rows)

    print(f"wrote {OUTPUT}")
    print(f"rows: {len(all_rows)}")
    print("by group:", dict(group_counts))
    print("by ai_screen_code:", dict(code_counts))


if __name__ == "__main__":
    main()
