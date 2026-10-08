#!/usr/bin/env python3
"""Merge four-source tool/keep papers with DBLP manually screened tool papers.

Defaults:
  four-source input: all_ccf_a_long_papers_all_categories_ai_screened.csv
    - keeps rows with ai_screen_code == 3
  DBLP input: dblp_ccf_a_2024_plus_tool_papers.csv
    - keeps rows with manual_tool_keep == yes

Deduplication:
  1. merge rows sharing a normalized DOI
  2. merge rows sharing a normalized title

The output keeps the union of all input columns and appends merge provenance
columns so each merged row can be traced back to the original source rows.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


Row = Dict[str, str]

DEFAULT_FOUR_SOURCE = "all_ccf_a_long_papers_all_categories_ai_screened.csv"
DEFAULT_DBLP = "dblp_ccf_a_2024_plus_tool_papers.csv"
DEFAULT_OUTPUT = "all_tool_papers_with_dblp_merged.csv"
DEFAULT_DUPLICATES_OUTPUT = "all_tool_papers_with_dblp_duplicate_groups.csv"

MERGE_METADATA_COLUMNS = [
    "tool_merge_sources",
    "tool_merge_has_four_source",
    "tool_merge_has_dblp",
    "tool_merge_input_files",
    "tool_merge_input_rows",
    "tool_merge_record_count",
    "tool_merge_dedupe_keys",
]

PREFERRED_COLUMNS = [
    *MERGE_METADATA_COLUMNS,
    "manual_source_index",
    "manual_tool_keep",
    "tool_name_or_method",
    "manual_tool_scope",
    "manual_tool_confidence",
    "manual_screen_reason",
    "ai_screen_code",
    "ai_screen_category",
    "ai_screen_category_zh",
    "ai_screen_reason",
    "ccf_rank",
    "ccf_area_group",
    "ccf_area",
    "ccf_venue",
    "ccf_venue_kind",
    "ccf_match_field",
    "ccf_match_value",
    "paper_pages",
    "is_long_paper",
    "long_paper_reason",
    "title",
    "author",
    "year",
    "journal",
    "booktitle",
    "series",
    "venue",
    "venue_type",
    "venue_detail",
    "publisher",
    "doi",
    "url",
    "abstract",
    "keywords",
    "paper_sources",
    "source_csvs",
    "source_records",
    "merged_record_count",
    "dedupe_keys",
]

BEST_VALUE_FIELDS = {
    "title",
    "author",
    "abstract",
    "year",
    "venue",
    "venue_detail",
    "booktitle",
    "journal",
}


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


def title_key(row: Row) -> str:
    key = normalize_title(row.get("title", ""))
    if len(key) < 16 or len(key.split()) < 3:
        return ""
    return key


def detail_score(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]", clean_text(value)))


def author_score(value: str) -> int:
    separators = len(re.findall(r"\band\b|,|;", value or "", flags=re.IGNORECASE))
    return separators * 20 + detail_score(value)


def extract_years(value: str) -> list[int]:
    return [int(match) for part in split_values(value) for match in re.findall(r"(?:19|20)\d{2}", part)]


def choose_best(values: Iterable[str], field: str) -> str:
    candidates = [part for value in values for part in split_values(value)]
    if not candidates:
        return ""
    if field == "year":
        years = [str(year) for value in candidates for year in extract_years(value)]
        if years:
            return max(years)
    if field == "author":
        return max(candidates, key=lambda value: (author_score(value), len(value)))
    return max(candidates, key=lambda value: (detail_score(value), len(value)))


def row_id(row: Row) -> str:
    return f"{row['_merge_kind']}:{row['_merge_input_file']}:#{row['_merge_input_row']}"


def read_four_source(path: Path, keep_code: str) -> Tuple[List[str], List[Row]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows: list[Row] = []
        for index, raw in enumerate(reader, start=1):
            row = {field: clean_text(raw.get(field, "")) for field in fields}
            if clean_text(row.get("ai_screen_code", "")) != keep_code:
                continue
            row["_merge_kind"] = "four_sources"
            row["_merge_input_file"] = path.name
            row["_merge_input_row"] = str(index)
            row["_merge_title_key"] = title_key(row)
            rows.append(row)
    return fields, rows


def read_dblp(path: Path) -> Tuple[List[str], List[Row]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows: list[Row] = []
        for index, raw in enumerate(reader, start=1):
            row = {field: clean_text(raw.get(field, "")) for field in fields}
            keep = clean_text(row.get("manual_tool_keep", "yes")).casefold()
            if keep not in {"", "yes", "true", "1"}:
                continue
            row["_merge_kind"] = "DBLP"
            row["_merge_input_file"] = path.name
            row["_merge_input_row"] = str(index)
            row["_merge_title_key"] = title_key(row)
            rows.append(row)
    return fields, rows


def grouped_records(rows: Sequence[Row]) -> list[list[Row]]:
    dsu = DisjointSet(len(rows))
    doi_owner: dict[str, int] = {}
    title_owner: dict[str, int] = {}

    for index, row in enumerate(rows):
        for doi in doi_values(row.get("doi", "")):
            if doi in doi_owner:
                dsu.union(index, doi_owner[doi])
            else:
                doi_owner[doi] = index

        key = row.get("_merge_title_key", "")
        if key:
            if key in title_owner:
                dsu.union(index, title_owner[key])
            else:
                title_owner[key] = index

    groups: dict[int, list[tuple[int, Row]]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[dsu.find(index)].append((index, row))

    ordered = sorted(groups.values(), key=lambda group: min(index for index, _row in group))
    return [[row for _index, row in group] for group in ordered]


def build_output_columns(input_fields: Sequence[str]) -> list[str]:
    columns: list[str] = []
    for field in PREFERRED_COLUMNS:
        if field not in columns:
            columns.append(field)
    for field in input_fields:
        if field not in columns and not field.startswith("_"):
            columns.append(field)
    return columns


def merge_field(rows: Sequence[Row], field: str) -> str:
    values = [row.get(field, "") for row in rows]
    if field in BEST_VALUE_FIELDS:
        return choose_best(values, field)
    return distinct_values(values)


def merge_group(rows: Sequence[Row], output_columns: Sequence[str]) -> Row:
    merged: Row = {field: "" for field in output_columns}

    for field in output_columns:
        if field in MERGE_METADATA_COLUMNS:
            continue
        merged[field] = merge_field(rows, field)

    merge_sources = distinct_values(row.get("_merge_kind", "") for row in rows)
    merged["tool_merge_sources"] = merge_sources
    merged["tool_merge_has_four_source"] = "yes" if any(row.get("_merge_kind") == "four_sources" for row in rows) else "no"
    merged["tool_merge_has_dblp"] = "yes" if any(row.get("_merge_kind") == "DBLP" for row in rows) else "no"
    merged["tool_merge_input_files"] = distinct_values(row.get("_merge_input_file", "") for row in rows)
    merged["tool_merge_input_rows"] = distinct_values(row_id(row) for row in rows)
    merged["tool_merge_record_count"] = str(len(rows))

    doi_keys = [f"doi:{doi}" for row in rows for doi in doi_values(row.get("doi", ""))]
    title_keys = [f"title:{row['_merge_title_key']}" for row in rows if row.get("_merge_title_key")]
    merged["tool_merge_dedupe_keys"] = distinct_values(doi_keys + title_keys)
    return merged


def duplicate_group_rows(groups: Sequence[Sequence[Row]]) -> list[Row]:
    output: list[Row] = []
    for group_index, group in enumerate(groups, start=1):
        if len(group) < 2:
            continue
        output.append(
            {
                "duplicate_group": str(group_index),
                "group_size": str(len(group)),
                "merge_sources": distinct_values(row.get("_merge_kind", "") for row in group),
                "titles": distinct_values(row.get("title", "") for row in group),
                "dois": distinct_values(row.get("doi", "") for row in group),
                "input_rows": distinct_values(row_id(row) for row in group),
            }
        )
    return output


def write_csv(path: Path, rows: Sequence[Row], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge four-source tool papers with DBLP screened tool papers.")
    parser.add_argument("--four-source-input", default=DEFAULT_FOUR_SOURCE, help="Four-source AI screened CSV.")
    parser.add_argument("--dblp-input", default=DEFAULT_DBLP, help="DBLP manually screened tool CSV.")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="Merged output CSV.")
    parser.add_argument("--duplicates-output", default=DEFAULT_DUPLICATES_OUTPUT, help="Duplicate-group report CSV.")
    parser.add_argument("--four-source-keep-code", default="3", help="ai_screen_code value to keep from four-source input.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    four_path = Path(args.four_source_input)
    dblp_path = Path(args.dblp_input)

    missing = [str(path) for path in (four_path, dblp_path) if not path.exists()]
    if missing:
        raise SystemExit("missing input files: " + ", ".join(missing))

    four_fields, four_rows = read_four_source(four_path, args.four_source_keep_code)
    dblp_fields, dblp_rows = read_dblp(dblp_path)
    all_rows = four_rows + dblp_rows
    output_columns = build_output_columns(four_fields + dblp_fields)

    groups = grouped_records(all_rows)
    merged_rows = [merge_group(group, output_columns) for group in groups]

    write_csv(Path(args.output), merged_rows, output_columns)
    duplicate_rows = duplicate_group_rows(groups)
    write_csv(
        Path(args.duplicates_output),
        duplicate_rows,
        ["duplicate_group", "group_size", "merge_sources", "titles", "dois", "input_rows"],
    )

    both_count = sum(1 for row in merged_rows if row["tool_merge_has_four_source"] == "yes" and row["tool_merge_has_dblp"] == "yes")
    four_only = sum(1 for row in merged_rows if row["tool_merge_has_four_source"] == "yes" and row["tool_merge_has_dblp"] == "no")
    dblp_only = sum(1 for row in merged_rows if row["tool_merge_has_four_source"] == "no" and row["tool_merge_has_dblp"] == "yes")

    print(f"four-source kept rows: {len(four_rows)}", file=sys.stderr)
    print(f"dblp kept rows: {len(dblp_rows)}", file=sys.stderr)
    print(f"input rows: {len(all_rows)}", file=sys.stderr)
    print(f"merged rows: {len(merged_rows)}", file=sys.stderr)
    print(f"duplicate groups merged: {len(duplicate_rows)}", file=sys.stderr)
    print(f"four-source only: {four_only}", file=sys.stderr)
    print(f"dblp only: {dblp_only}", file=sys.stderr)
    print(f"both sources: {both_count}", file=sys.stderr)
    print(args.output)
    print(args.duplicates_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
