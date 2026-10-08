#!/usr/bin/env python3
"""Merge ScienceDirect BibTeX exports into the shared paper CSV schema.

Default input pattern:
  scienceDirect/ScienceDirect_citations_*.bib

The output columns intentionally match acm_bib_merged.csv, ieee_bib_merged.csv,
and spring_all_paper.csv. Fields not present in ScienceDirect's BibTeX export
are written as empty strings.

Usage:
  python3 sciencedirect_bib_to_csv.py
  python3 sciencedirect_bib_to_csv.py -o sciencedirect_all_paper.csv
  python3 sciencedirect_bib_to_csv.py scienceDirect/ScienceDirect_citations_1781267052354.bib --dedupe
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from acm_bib_to_csv import merge_duplicate_records, parse_bib_file


Record = Dict[str, str]

DEFAULT_PATTERN = "scienceDirect/ScienceDirect_citations_*.bib"

SHARED_COLUMNS = [
    "source_file",
    "source_index",
    "entry_type",
    "citation_key",
    "title",
    "author",
    "year",
    "journal",
    "booktitle",
    "series",
    "publisher",
    "doi",
    "url",
    "abstract",
    "keywords",
    "address",
    "articleno",
    "edition",
    "editor",
    "isbn",
    "issn",
    "issue_date",
    "location",
    "month",
    "note",
    "number",
    "numpages",
    "pages",
    "volume",
]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_doi(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def page_count(pages: str) -> str:
    match = re.search(r"(\d+)\s*[-–]\s*(\d+)", pages or "")
    if not match:
        return ""

    start, end = int(match.group(1)), int(match.group(2))
    if end >= start:
        return str(end - start + 1)
    return ""


def normalize_sciencedirect_record(record: Record) -> Record:
    row = {column: "" for column in SHARED_COLUMNS}
    for column in SHARED_COLUMNS:
        row[column] = clean_text(record.get(column, ""))

    row["doi"] = normalize_doi(row["doi"])

    if not row["publisher"]:
        row["publisher"] = "ScienceDirect"

    if not row["url"] and row["doi"]:
        row["url"] = f"https://doi.org/{row['doi']}"

    if not row["numpages"] and row["pages"]:
        row["numpages"] = page_count(row["pages"])

    return row


def default_inputs() -> List[Path]:
    return sorted(Path().glob(DEFAULT_PATTERN))


def unique_records(records: Iterable[Record]) -> List[Record]:
    return merge_duplicate_records(records)


def write_csv(path: Path, records: Sequence[Record]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SHARED_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge ScienceDirect BibTeX exports into sciencedirect_all_paper.csv.")
    parser.add_argument("inputs", nargs="*", help=f"Input .bib files. Default glob: {DEFAULT_PATTERN}")
    parser.add_argument("-o", "--output", default="sciencedirect_all_paper.csv", help="Output CSV path.")
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate rows by DOI/citation key/title after merging.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = [Path(value) for value in args.inputs] if args.inputs else default_inputs()
    if not paths:
        raise SystemExit(f"no input files found for pattern: {DEFAULT_PATTERN}")

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing input files: " + ", ".join(missing))

    records: List[Record] = []
    for path in paths:
        file_records = parse_bib_file(path)
        print(f"{path}: {len(file_records)} records", file=sys.stderr)
        records.extend(file_records)

    rows = [normalize_sciencedirect_record(record) for record in records]
    before = len(rows)
    if args.dedupe:
        rows = unique_records(rows)

    write_csv(Path(args.output), rows)
    print(f"input records: {before}", file=sys.stderr)
    print(f"output records: {len(rows)}", file=sys.stderr)
    if args.dedupe:
        print(f"deduped {before} input records to {len(rows)} unique records", file=sys.stderr)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
