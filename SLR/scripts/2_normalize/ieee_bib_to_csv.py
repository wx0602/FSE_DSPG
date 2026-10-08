#!/usr/bin/env python3
"""Merge IEEE Xplore BibTeX downloads into an ACM-compatible CSV schema.

Default input pattern:
  ieee/IEEE Xplore Citation BibTeX Download*.bib

The output columns intentionally match acm_bib_merged.csv:
  source_file, source_index, entry_type, citation_key, title, author, year,
  journal, booktitle, series, publisher, doi, url, abstract, keywords, address,
  articleno, edition, editor, isbn, issn, issue_date, location, month, note,
  number, numpages, pages, volume

Usage:
  python3 ieee_bib_to_csv.py
  python3 ieee_bib_to_csv.py "ieee/IEEE Xplore Citation BibTeX Download 2026.6.12.16.25.6.bib" -o ieee_bib_merged.csv
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

DEFAULT_PATTERN = "ieee/IEEE Xplore Citation BibTeX Download*.bib"

ACM_COMPAT_COLUMNS = [
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


def page_count(pages: str) -> str:
    parts = re.findall(r"\d+", pages or "")
    if len(parts) >= 2:
        start, end = int(parts[0]), int(parts[-1])
        if end >= start:
            return str(end - start + 1)
    if len(parts) == 1:
        return "1"
    return ""


def normalize_month(value: str) -> str:
    value = clean_text(value).rstrip(".,")
    months = {
        "january": "jan",
        "february": "feb",
        "march": "mar",
        "april": "apr",
        "may": "may",
        "june": "jun",
        "july": "jul",
        "august": "aug",
        "september": "sep",
        "october": "oct",
        "november": "nov",
        "december": "dec",
    }
    return months.get(value.lower(), value)


def extract_series(booktitle: str) -> str:
    text = clean_text(booktitle)
    paren_values = re.findall(r"\(([A-Za-z][A-Za-z0-9&/ .+'-]{1,40})\)", text)
    if paren_values:
        return clean_text(paren_values[-1])

    known = (
        "ICSE",
        "ASE",
        "ISSTA",
        "FSE",
        "CCS",
        "S&P",
        "SP",
        "KDD",
        "SIGIR",
        "WWW",
        "CVPR",
        "ICCV",
        "ECCV",
        "ICML",
        "ICLR",
        "NeurIPS",
        "AAAI",
        "IJCAI",
    )
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", text).lower()
    for item in known:
        token = re.sub(r"[^A-Za-z0-9]+", " ", item).strip().lower()
        if re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", normalized):
            return item
    return ""


def normalize_ieee_record(record: Record) -> Record:
    row = {column: "" for column in ACM_COMPAT_COLUMNS}
    for column in ACM_COMPAT_COLUMNS:
        row[column] = clean_text(record.get(column, ""))

    doi = row["doi"]
    if doi and not row["url"]:
        row["url"] = f"https://doi.org/{doi}"

    if not row["publisher"]:
        row["publisher"] = "IEEE"

    if not row["numpages"] and row["pages"]:
        row["numpages"] = page_count(row["pages"])

    if row["booktitle"] and not row["series"]:
        row["series"] = extract_series(row["booktitle"])

    if row["month"]:
        row["month"] = normalize_month(row["month"])

    return row


def default_inputs() -> List[Path]:
    return sorted(Path().glob(DEFAULT_PATTERN))


def write_csv(path: Path, records: Sequence[Record]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ACM_COMPAT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge IEEE Xplore BibTeX downloads into an ACM-compatible CSV.")
    parser.add_argument("inputs", nargs="*", help=f"Input .bib files. Default glob: {DEFAULT_PATTERN}")
    parser.add_argument("-o", "--output", default="ieee_bib_merged.csv", help="Output CSV path.")
    parser.add_argument("--no-dedupe", action="store_true", help="Keep raw rows instead of merging duplicates.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = [Path(value) for value in args.inputs] if args.inputs else default_inputs()
    if not paths:
        raise SystemExit(f"no input files found for pattern: {DEFAULT_PATTERN}")

    records: List[Record] = []
    for path in paths:
        file_records = parse_bib_file(path)
        print(f"{path}: {len(file_records)} records", file=sys.stderr)
        records.extend(file_records)

    before = len(records)
    if not args.no_dedupe:
        records = merge_duplicate_records(records)

    rows = [normalize_ieee_record(record) for record in records]
    write_csv(Path(args.output), rows)

    print(f"input records: {before}", file=sys.stderr)
    print(f"output records: {len(rows)}", file=sys.stderr)
    if not args.no_dedupe:
        print(f"deduped {before} input records to {len(rows)} unique records", file=sys.stderr)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
