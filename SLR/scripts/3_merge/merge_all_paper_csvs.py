#!/usr/bin/env python3
"""Merge ACM, IEEE, SpringerLink, and ScienceDirect CSV files with deduplication.

Default inputs:
  acm_bib_merged.csv
  ieee_bib_merged.csv
  spring_all_paper.csv
  sciencedirect_all_paper.csv

Deduplication:
  1. Rows with the same normalized DOI are merged.
  2. Rows with the same normalized title are merged, even when year or DOI
     values differ. Conflicting values are kept with " || " separators.

The merged output keeps the shared source columns and appends provenance and
venue helper columns.

Usage:
  python3 merge_all_paper_csvs.py
  python3 merge_all_paper_csvs.py -o all_papers_merged_dedup.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


Record = Dict[str, str]

DEFAULT_INPUTS = (
    "acm_bib_merged.csv",
    "ieee_bib_merged.csv",
    "spring_all_paper.csv",
    "sciencedirect_all_paper.csv",
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

EXTRA_COLUMNS = [
    "venue_type",
    "venue",
    "venue_detail",
    "paper_sources",
    "source_csvs",
    "source_records",
    "merged_record_count",
    "dedupe_keys",
]

OUTPUT_COLUMNS = SHARED_COLUMNS + EXTRA_COLUMNS

MERGE_DISTINCT_FIELDS = {
    "source_file",
    "source_index",
    "citation_key",
    "journal",
    "booktitle",
    "series",
    "publisher",
    "doi",
    "url",
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
}

BEST_VALUE_FIELDS = {
    "entry_type",
    "title",
    "author",
    "year",
    "abstract",
}

SOURCE_LABELS = {
    "acm_bib_merged.csv": "ACM",
    "ieee_bib_merged.csv": "IEEE",
    "spring_all_paper.csv": "SpringerLink",
    "sciencedirect_all_paper.csv": "ScienceDirect",
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
    text = html.unescape(value or "")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def split_merged_values(value: str) -> List[str]:
    parts = []
    for part in re.split(r"\s+\|\|\s+", value or ""):
        text = clean_text(part)
        if text:
            parts.append(text)
    return parts


def distinct_values(values: Iterable[str], sep: str = " || ") -> str:
    output: List[str] = []
    seen = set()
    for value in values:
        for part in split_merged_values(value):
            key = canonical_value(part)
            if key and key not in seen:
                seen.add(key)
                output.append(part)
    return sep.join(output)


def canonical_value(value: str) -> str:
    text = clean_text(value).casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .;,")


def normalize_doi(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.strip().strip(".;,").casefold()


def doi_values(value: str) -> List[str]:
    return [doi for doi in (normalize_doi(part) for part in split_merged_values(value)) if doi]


def normalize_year(value: str) -> str:
    match = re.search(r"(19|20)\d{2}", value or "")
    return match.group(0) if match else clean_text(value)


def normalize_title(value: str) -> str:
    text = clean_text(value).casefold()
    text = re.sub(r"[{}\\]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_valid_title_key(title_key: str) -> bool:
    tokens = title_key.split()
    return len(title_key) >= 16 and len(tokens) >= 3


def title_key(row: Record) -> str:
    title_key = normalize_title(row.get("title", ""))
    if not is_valid_title_key(title_key):
        return ""
    return title_key


def source_label(path: Path) -> str:
    return SOURCE_LABELS.get(path.name, path.stem)


def read_csv(path: Path) -> List[Record]:
    records: List[Record] = []
    label = source_label(path)
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=1):
            record = {column: clean_text(row.get(column, "")) for column in SHARED_COLUMNS}
            record["_source_csv"] = path.name
            record["_paper_source"] = label
            record["_input_row_number"] = str(row_number)
            record["_doi_keys"] = " || ".join(doi_values(record.get("doi", "")))
            record["_title_key"] = title_key(record)
            records.append(record)
    return records


def union_by_doi(records: Sequence[Record], dsu: DisjointSet) -> None:
    owners: Dict[str, int] = {}
    for index, record in enumerate(records):
        for doi in doi_values(record.get("doi", "")):
            if doi in owners:
                dsu.union(index, owners[doi])
            else:
                owners[doi] = index


def union_by_title(records: Sequence[Record], dsu: DisjointSet) -> None:
    groups: Dict[str, List[int]] = defaultdict(list)
    for index, record in enumerate(records):
        key = record.get("_title_key", "")
        if key:
            groups[key].append(index)

    for indexes in groups.values():
        if len(indexes) < 2:
            continue
        anchor = indexes[0]
        for index in indexes[1:]:
            dsu.union(anchor, index)


def grouped_records(records: Sequence[Record]) -> List[List[Record]]:
    dsu = DisjointSet(len(records))
    union_by_doi(records, dsu)
    union_by_title(records, dsu)

    groups: Dict[int, List[Tuple[int, Record]]] = defaultdict(list)
    for index, record in enumerate(records):
        groups[dsu.find(index)].append((index, record))

    ordered_groups = sorted(groups.values(), key=lambda group: min(index for index, _record in group))
    return [[record for _index, record in group] for group in ordered_groups]


def choose_entry_type(values: Iterable[str]) -> str:
    priority = {
        "inproceedings": 70,
        "proceedings": 60,
        "article": 50,
        "inbook": 40,
        "book": 30,
        "misc": 20,
    }
    candidates = split_all_values(values)
    if not candidates:
        return ""
    return max(candidates, key=lambda value: (priority.get(value.casefold(), 0), len(value)))


def split_all_values(values: Iterable[str]) -> List[str]:
    output: List[str] = []
    for value in values:
        output.extend(split_merged_values(value))
    return output


def choose_year(values: Iterable[str]) -> str:
    years = [normalize_year(value) for value in split_all_values(values) if normalize_year(value)]
    if not years:
        return ""
    counts = Counter(years)
    return counts.most_common(1)[0][0]


def choose_best_value(values: Iterable[str], field: str) -> str:
    candidates = split_all_values(values)
    if not candidates:
        return ""
    if field == "entry_type":
        return choose_entry_type(candidates)
    if field == "year":
        return choose_year(candidates)
    if field == "author":
        return max(candidates, key=lambda value: (author_score(value), len(value)))
    return max(candidates, key=lambda value: (detail_score(value), len(value)))


def detail_score(value: str) -> int:
    text = clean_text(value)
    return len(re.findall(r"[A-Za-z0-9]", text))


def author_score(value: str) -> int:
    text = clean_text(value)
    separators = len(re.findall(r"\band\b|,|;", text, flags=re.IGNORECASE))
    return separators * 20 + detail_score(text)


def merge_keywords(values: Iterable[str]) -> str:
    output: List[str] = []
    seen = set()
    for value in split_all_values(values):
        for part in re.split(r"\s*[,;]\s*", value):
            keyword = clean_text(part)
            key = canonical_value(keyword)
            if keyword and key not in seen:
                seen.add(key)
                output.append(keyword)
    return "; ".join(output)


def merge_doi_field(values: Iterable[str]) -> str:
    dois: List[str] = []
    for value in values:
        dois.extend(doi_values(value))
    return distinct_values(dois)


def merge_field(records: Sequence[Record], field: str) -> str:
    values = [record.get(field, "") for record in records]
    if field == "doi":
        return merge_doi_field(values)
    if field == "keywords":
        return merge_keywords(values)
    if field in MERGE_DISTINCT_FIELDS:
        return distinct_values(values)
    if field in BEST_VALUE_FIELDS:
        return choose_best_value(values, field)
    return distinct_values(values)


def build_source_record(record: Record) -> str:
    parts = [record.get("_source_csv", "")]
    source_file = record.get("source_file", "")
    source_index = record.get("source_index", "")
    if source_file:
        parts.append(source_file)
    if source_index:
        parts.append("#" + source_index)
    return ":".join(part for part in parts if part)


def is_contained(shorter: str, longer: str) -> bool:
    short_key = canonical_value(shorter)
    long_key = canonical_value(longer)
    return bool(short_key and long_key and short_key in long_key)


def append_series(booktitle: str, series: str) -> str:
    if not booktitle:
        return series
    if not series:
        return booktitle
    if is_contained(series, booktitle):
        return booktitle
    return f"{booktitle} ({series})"


def build_venue_fields(row: Record) -> Tuple[str, str, str]:
    journal = row.get("journal", "")
    booktitle = row.get("booktitle", "")
    series = row.get("series", "")
    note = row.get("note", "")
    title = row.get("title", "")
    entry_type = canonical_value(row.get("entry_type", ""))
    title_looks_like_proceedings = bool(re.search(r"\b(proceedings|conference|symposium|workshop)\b", title, re.I))

    has_conference = bool(booktitle)
    has_journal = bool(journal)
    has_proceedings_title = not has_conference and not has_journal and title and (
        entry_type == "proceedings" or title_looks_like_proceedings
    )

    if has_conference and has_journal:
        venue_type = "conference/journal"
    elif has_conference:
        venue_type = "conference"
    elif has_journal:
        venue_type = "journal"
    elif series:
        venue_type = "series"
    elif has_proceedings_title:
        venue_type = "proceedings"
    else:
        venue_type = ""

    if has_conference:
        venue = append_series(booktitle, series)
    elif has_journal:
        venue = journal
    elif has_proceedings_title:
        venue = title
    else:
        venue = series

    detail_parts = []
    if has_proceedings_title:
        detail_parts.append("proceedings: " + title)
    if booktitle:
        detail_parts.append("booktitle: " + booktitle)
    if series:
        detail_parts.append("series: " + series)
    if journal:
        detail_parts.append("journal: " + journal)
    if row.get("volume", ""):
        detail_parts.append("volume: " + row["volume"])
    if row.get("number", ""):
        detail_parts.append("number: " + row["number"])
    if row.get("pages", ""):
        detail_parts.append("pages: " + row["pages"])
    if row.get("location", ""):
        detail_parts.append("location: " + row["location"])
    if row.get("publisher", ""):
        detail_parts.append("publisher: " + row["publisher"])
    if row.get("year", ""):
        detail_parts.append("year: " + row["year"])
    if note:
        detail_parts.append("note: " + note)

    return venue_type, venue, " | ".join(detail_parts)


def merge_group(records: Sequence[Record]) -> Record:
    row = {column: merge_field(records, column) for column in SHARED_COLUMNS}

    venue_type, venue, venue_detail = build_venue_fields(row)
    row["venue_type"] = venue_type
    row["venue"] = venue
    row["venue_detail"] = venue_detail
    row["paper_sources"] = distinct_values(record.get("_paper_source", "") for record in records)
    row["source_csvs"] = distinct_values(record.get("_source_csv", "") for record in records)
    row["source_records"] = distinct_values(build_source_record(record) for record in records)
    row["merged_record_count"] = str(len(records))

    doi_keys = [f"doi:{doi}" for record in records for doi in doi_values(record.get("doi", ""))]
    title_keys = [f"title:{record['_title_key']}" for record in records if record.get("_title_key", "")]
    row["dedupe_keys"] = distinct_values(doi_keys + title_keys)
    return row


def write_csv(path: Path, records: Sequence[Record]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge and deduplicate paper CSV files from four sources.")
    parser.add_argument("inputs", nargs="*", help="Input CSV files. Defaults to the four generated source CSVs.")
    parser.add_argument("-o", "--output", default="all_papers_merged_dedup.csv", help="Output merged CSV path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = [Path(value) for value in args.inputs] if args.inputs else [Path(value) for value in DEFAULT_INPUTS]

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing input files: " + ", ".join(missing))

    records: List[Record] = []
    for path in paths:
        file_records = read_csv(path)
        print(f"{path}: {len(file_records)} records", file=sys.stderr)
        records.extend(file_records)

    groups = grouped_records(records)
    merged_rows = [merge_group(group) for group in groups]
    write_csv(Path(args.output), merged_rows)

    duplicate_groups = sum(1 for group in groups if len(group) > 1)
    print(f"input records: {len(records)}", file=sys.stderr)
    print(f"output records: {len(merged_rows)}", file=sys.stderr)
    print(f"duplicate groups merged: {duplicate_groups}", file=sys.stderr)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
