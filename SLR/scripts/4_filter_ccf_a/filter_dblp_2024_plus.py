#!/usr/bin/env python3
"""Filter the deduplicated DBLP metadata table to papers from 2024 onward."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Sequence


Record = Dict[str, str]


def split_values(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s+\|\|\s+|;", value or "") if part.strip()]


def extract_years(value: str) -> list[int]:
    years: list[int] = []
    for part in split_values(value):
        for match in re.findall(r"(?:19|20)\d{2}", part):
            years.append(int(match))
    return years


def read_csv(path: Path) -> tuple[list[str], list[Record]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Record]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter DBLP papers to a minimum publication year.")
    parser.add_argument("-i", "--input", default="dblp_all_paper_dedup.csv", help="Input DBLP CSV.")
    parser.add_argument("-o", "--output", default="dblp_all_paper_dedup_2024_plus.csv", help="Output filtered CSV.")
    parser.add_argument("--min-year", type=int, default=2024, help="Minimum publication year. Default: 2024.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"input file not found: {input_path}")

    fieldnames, rows = read_csv(input_path)
    for extra in ("year_values", "year_filter_min"):
        if extra not in fieldnames:
            fieldnames.append(extra)

    filtered: list[Record] = []
    for row in rows:
        years = sorted(set(extract_years(row.get("year", ""))))
        row["year_values"] = " || ".join(str(year) for year in years)
        row["year_filter_min"] = str(args.min_year)
        if any(year >= args.min_year for year in years):
            filtered.append(row)

    write_csv(Path(args.output), fieldnames, filtered)
    print(f"input rows: {len(rows)}", file=sys.stderr)
    print(f"output rows: {len(filtered)}", file=sys.stderr)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
