#!/usr/bin/env python3
"""Merge the two SpringerLink search-result CSV files into one paper CSV.

Default inputs:
  spring/SearchResults2425.csv
  spring/SearchResults26.csv

The output columns intentionally match acm_bib_merged.csv and ieee_bib_merged.csv.
Fields not present in SpringerLink's search export are written as empty strings.

Usage:
  python3 spring_csv_to_csv.py
  python3 spring_csv_to_csv.py -o spring_all_paper.csv
  python3 spring_csv_to_csv.py spring/SearchResults2425.csv spring/SearchResults26.csv --dedupe
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


Record = Dict[str, str]

DEFAULT_INPUTS = (
    "spring/SearchResults2425.csv",
    "spring/SearchResults26.csv",
)

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
    text = html.unescape(value or "")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def entry_type_from_content_type(content_type: str) -> str:
    value = clean_text(content_type).lower()
    if value == "article":
        return "article"
    if value in {"conference paper", "conferencepaper"}:
        return "inproceedings"
    if value in {"chapter", "book chapter"}:
        return "inbook"
    if value == "book":
        return "book"
    return value.replace(" ", "_")


def source_key(record: Record) -> str:
    doi = clean_text(record.get("doi", "")).lower()
    if doi:
        return "doi:" + doi
    url = clean_text(record.get("url", "")).lower()
    if url:
        return "url:" + url
    title = clean_text(record.get("title", "")).lower()
    year = clean_text(record.get("year", ""))
    return f"title:{title}|{year}"


def unique_records(records: Iterable[Record]) -> List[Record]:
    seen = set()
    output = []
    for record in records:
        key = source_key(record)
        if key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output


def normalize_spring_row(row: Dict[str, str], source_file: str, source_index: int) -> Record:
    output = {column: "" for column in SHARED_COLUMNS}

    title = clean_text(row.get("Item Title", ""))
    publication_title = clean_text(row.get("Publication Title", ""))
    book_series_title = clean_text(row.get("Book Series Title", ""))
    content_type = clean_text(row.get("Content Type", ""))
    entry_type = entry_type_from_content_type(content_type)
    doi = clean_text(row.get("Item DOI", ""))

    output["source_file"] = source_file
    output["source_index"] = str(source_index)
    output["entry_type"] = entry_type
    output["citation_key"] = doi
    output["title"] = title
    output["author"] = clean_text(row.get("Authors", ""))
    output["year"] = clean_text(row.get("Publication Year", ""))
    output["publisher"] = "SpringerLink"
    output["doi"] = doi
    output["url"] = clean_text(row.get("URL", ""))
    output["series"] = book_series_title
    output["volume"] = clean_text(row.get("Journal Volume", ""))
    output["number"] = clean_text(row.get("Journal Issue", ""))

    if entry_type == "article":
        output["journal"] = publication_title
    elif entry_type in {"inproceedings", "inbook", "book"}:
        output["booktitle"] = publication_title
    else:
        output["journal"] = publication_title

    return output


def read_spring_csv(path: Path) -> List[Record]:
    records: List[Record] = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            records.append(normalize_spring_row(row, path.name, index))
    return records


def default_inputs() -> List[Path]:
    return [Path(value) for value in DEFAULT_INPUTS]


def write_csv(path: Path, records: Sequence[Record]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SHARED_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge SpringerLink CSV exports into spring_all_paper.csv.")
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input CSV files. Default: spring/SearchResults2425.csv spring/SearchResults26.csv",
    )
    parser.add_argument("-o", "--output", default="spring_all_paper.csv", help="Output CSV path.")
    parser.add_argument("--dedupe", action="store_true", help="Deduplicate rows by DOI/URL/title after merging.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = [Path(value) for value in args.inputs] if args.inputs else default_inputs()
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing input files: " + ", ".join(missing))

    records: List[Record] = []
    for path in paths:
        file_records = read_spring_csv(path)
        print(f"{path}: {len(file_records)} records", file=sys.stderr)
        records.extend(file_records)

    before = len(records)
    if args.dedupe:
        records = unique_records(records)

    write_csv(Path(args.output), records)
    print(f"input records: {before}", file=sys.stderr)
    print(f"output records: {len(records)}", file=sys.stderr)
    if args.dedupe:
        print(f"deduped {before} input records to {len(records)} unique records", file=sys.stderr)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
