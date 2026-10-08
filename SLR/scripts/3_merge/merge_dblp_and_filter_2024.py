#!/usr/bin/env python3
"""Merge the existing paper table with DBLP results and keep 2024+ papers.

Default inputs:
  all_papers_merged_dedup.csv
  dblp_all_paper_dedup.csv

Outputs:
  all_sources_with_dblp_2024_plus.csv
  dblp_all_paper_dedup_2024_plus.csv

Deduplication uses normalized DOI first and normalized title second. When rows
are merged, distinct non-empty values are kept with " || " separators.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


Record = Dict[str, str]

DEFAULT_INPUTS = [
    "all_papers_merged_dedup.csv",
    "dblp_all_paper_dedup.csv",
]

COMMON_FIRST_COLUMNS = [
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
    "venue_type",
    "venue",
    "venue_detail",
]

MERGE_LAST_COLUMNS = [
    "paper_sources",
    "source_csvs",
    "source_records",
    "merged_record_count",
    "dedupe_keys",
    "year_values",
    "year_filter_min",
]

BEST_VALUE_FIELDS = {"title", "author", "abstract", "entry_type", "year"}


class DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def clean_text(value: str) -> str:
    text = html.unescape(value or "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def split_values(value: str) -> list[str]:
    return [clean_text(part) for part in re.split(r"\s+\|\|\s+", value or "") if clean_text(part)]


def canonical_value(value: str) -> str:
    return clean_text(value).casefold().strip(" .;,")


def distinct_values(values: Iterable[str], sep: str = " || ") -> str:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        for part in split_values(value):
            key = canonical_value(part)
            if key and key not in seen:
                seen.add(key)
                output.append(part)
    return sep.join(output)


def normalize_doi(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.strip().strip(".;,").casefold()


def doi_values(value: str) -> list[str]:
    return [doi for doi in (normalize_doi(part) for part in split_values(value)) if doi]


def normalize_title(value: str) -> str:
    text = clean_text(value).casefold()
    text = re.sub(r"[{}\\]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_key(row: Record) -> str:
    key = normalize_title(row.get("title", ""))
    if len(key) < 16 or len(key.split()) < 3:
        return ""
    return key


def extract_years(value: str) -> list[int]:
    years: list[int] = []
    for part in split_values(value):
        for match in re.findall(r"(?:19|20)\d{2}", part):
            years.append(int(match))
    return years


def has_year_at_least(row: Record, min_year: int) -> bool:
    return any(year >= min_year for year in extract_years(row.get("year_values", row.get("year", ""))))


def detail_score(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]", clean_text(value)))


def author_score(value: str) -> int:
    separators = len(re.findall(r"\band\b|,|;", value or "", flags=re.IGNORECASE))
    return separators * 20 + detail_score(value)


def choose_best(values: Iterable[str], field: str) -> str:
    candidates: list[str] = []
    for value in values:
        candidates.extend(split_values(value))
    candidates = [value for value in candidates if value]
    if not candidates:
        return ""
    if field == "year":
        years = [str(year) for value in candidates for year in extract_years(value)]
        if years:
            return max(years)
    if field == "author":
        return max(candidates, key=lambda value: (author_score(value), len(value)))
    return max(candidates, key=lambda value: (detail_score(value), len(value)))


def source_label(path: Path, row: Record) -> str:
    if path.name == "dblp_all_paper_dedup.csv":
        return "DBLP"
    if row.get("paper_sources"):
        return row["paper_sources"]
    return path.stem


def source_record(path: Path, row: Record, row_number: int) -> str:
    if row.get("source_records"):
        return row["source_records"]
    source_file = row.get("source_file") or path.name
    source_index = row.get("source_index") or str(row_number)
    return f"{path.name}:{source_file}:#{source_index}"


def read_csv(path: Path) -> tuple[list[str], list[Record]]:
    records: list[Record] = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        for row_number, row in enumerate(reader, start=1):
            record = {field: clean_text(row.get(field, "")) for field in fieldnames}
            record["_source_csv"] = path.name
            record["_paper_source"] = source_label(path, record)
            record["_source_record"] = source_record(path, record, row_number)
            record["_title_key"] = title_key(record)
            records.append(record)
    return fieldnames, records


def build_output_columns(input_fields: Sequence[str]) -> list[str]:
    columns: list[str] = []
    for field in COMMON_FIRST_COLUMNS:
        if field not in columns:
            columns.append(field)
    for field in input_fields:
        if field not in columns and field not in MERGE_LAST_COLUMNS:
            columns.append(field)
    for field in MERGE_LAST_COLUMNS:
        if field not in columns:
            columns.append(field)
    return columns


def grouped_records(records: Sequence[Record]) -> list[list[Record]]:
    dsu = DisjointSet(len(records))
    doi_owner: dict[str, int] = {}
    title_owner: dict[str, int] = {}

    for index, record in enumerate(records):
        for doi in doi_values(record.get("doi", "")):
            if doi in doi_owner:
                dsu.union(index, doi_owner[doi])
            else:
                doi_owner[doi] = index

        key = record.get("_title_key", "")
        if key:
            if key in title_owner:
                dsu.union(index, title_owner[key])
            else:
                title_owner[key] = index

    groups: dict[int, list[tuple[int, Record]]] = defaultdict(list)
    for index, record in enumerate(records):
        groups[dsu.find(index)].append((index, record))

    ordered = sorted(groups.values(), key=lambda group: min(index for index, _record in group))
    return [[record for _index, record in group] for group in ordered]


def parse_merged_count(record: Record) -> int:
    try:
        return int(record.get("merged_record_count", "1") or "1")
    except ValueError:
        return 1


def merge_group(records: Sequence[Record], output_columns: Sequence[str], min_year: int) -> Record:
    row: Record = {field: "" for field in output_columns}
    for field in output_columns:
        if field in {"paper_sources", "source_csvs", "source_records", "merged_record_count", "dedupe_keys", "year_values", "year_filter_min"}:
            continue

        values = [record.get(field, "") for record in records]
        if field in BEST_VALUE_FIELDS:
            row[field] = choose_best(values, field)
        else:
            row[field] = distinct_values(values)

    row["paper_sources"] = distinct_values(record.get("_paper_source", "") for record in records)
    row["source_csvs"] = distinct_values(record.get("_source_csv", "") for record in records)
    row["source_records"] = distinct_values(record.get("_source_record", "") for record in records)
    row["merged_record_count"] = str(sum(parse_merged_count(record) for record in records))

    doi_keys = [f"doi:{doi}" for record in records for doi in doi_values(record.get("doi", ""))]
    title_keys = [f"title:{record['_title_key']}" for record in records if record.get("_title_key")]
    row["dedupe_keys"] = distinct_values(doi_keys + title_keys)

    years = sorted({year for record in records for year in extract_years(record.get("year", ""))})
    row["year_values"] = " || ".join(str(year) for year in years)
    row["year_filter_min"] = str(min_year)
    return row


def write_csv(path: Path, rows: Sequence[Record], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def filter_rows_by_year(rows: Sequence[Record], min_year: int) -> list[Record]:
    return [row for row in rows if has_year_at_least(row, min_year)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge existing paper metadata with DBLP and keep papers from a minimum year.")
    parser.add_argument("inputs", nargs="*", help=f"Input CSVs. Default: {', '.join(DEFAULT_INPUTS)}")
    parser.add_argument("--min-year", type=int, default=2024, help="Minimum publication year to keep. Default: 2024.")
    parser.add_argument("--output", default="all_sources_with_dblp_2024_plus.csv", help="Merged 2024+ output CSV.")
    parser.add_argument("--dblp-output", default="dblp_all_paper_dedup_2024_plus.csv", help="DBLP-only 2024+ output CSV.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = [Path(value) for value in args.inputs] if args.inputs else [Path(value) for value in DEFAULT_INPUTS]

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing input files: " + ", ".join(missing))

    input_fields: list[str] = []
    records: list[Record] = []
    dblp_rows: list[Record] = []
    dblp_fields: list[str] = []

    for path in paths:
        fields, file_records = read_csv(path)
        for field in fields:
            if field not in input_fields:
                input_fields.append(field)
        records.extend(file_records)
        if path.name == "dblp_all_paper_dedup.csv":
            dblp_fields = fields
            dblp_rows = file_records
        print(f"{path}: {len(file_records)} records", file=sys.stderr)

    output_columns = build_output_columns(input_fields)
    groups = grouped_records(records)
    merged_rows = [merge_group(group, output_columns, args.min_year) for group in groups]
    filtered_rows = filter_rows_by_year(merged_rows, args.min_year)

    write_csv(Path(args.output), filtered_rows, output_columns)

    if dblp_rows:
        dblp_output_fields = list(OrderedDict.fromkeys(dblp_fields + ["year_values", "year_filter_min"]))
        dblp_filtered: list[Record] = []
        for record in dblp_rows:
            year_values = " || ".join(str(year) for year in sorted(set(extract_years(record.get("year", "")))))
            record["year_values"] = year_values
            record["year_filter_min"] = str(args.min_year)
            if has_year_at_least(record, args.min_year):
                dblp_filtered.append(record)
        write_csv(Path(args.dblp_output), dblp_filtered, dblp_output_fields)
        print(f"dblp {args.min_year}+ records: {len(dblp_filtered)}", file=sys.stderr)

    duplicate_groups = sum(1 for group in groups if len(group) > 1)
    print(f"input records: {len(records)}", file=sys.stderr)
    print(f"merged all-year records: {len(merged_rows)}", file=sys.stderr)
    print(f"duplicate groups merged: {duplicate_groups}", file=sys.stderr)
    print(f"merged {args.min_year}+ records: {len(filtered_rows)}", file=sys.stderr)
    print(args.output)
    if dblp_rows:
        print(args.dblp_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
