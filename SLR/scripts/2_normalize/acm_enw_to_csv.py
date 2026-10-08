#!/usr/bin/env python3
"""Convert EndNote .enw records to CSV.

Usage:
  python3 acm_enw_to_csv.py acm.enw
  python3 acm_enw_to_csv.py acm.enw -o acm.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


TAG_RE = re.compile(r"^%([A-Za-z0-9@])\s*(.*)$")
SPACE_RE = re.compile(r"\s+")

FIELD_MAP = {
    "0": "reference_type",
    "T": "title",
    "A": "authors",
    "E": "editors",
    "D": "publication_date",
    "J": "journal",
    "B": "booktitle",
    "I": "publisher",
    "R": "doi",
    "U": "url",
    "K": "keywords",
    "X": "abstract",
    "@": "isbn_issn",
    "V": "volume",
    "N": "issue",
    "P": "pages",
    "C": "place",
    "Z": "notes",
}

LIST_FIELDS = {"authors", "editors", "keywords", "notes"}

CSV_COLUMNS = [
    "source",
    "record_index",
    "reference_type",
    "title",
    "authors",
    "editors",
    "year",
    "publication_date",
    "venue",
    "journal",
    "booktitle",
    "publisher",
    "doi",
    "url",
    "keywords",
    "abstract",
    "isbn_issn",
    "volume",
    "issue",
    "pages",
    "place",
    "notes",
    "extra_fields",
]


def clean_text(value: str) -> str:
    return SPACE_RE.sub(" ", value or "").strip()


def append_value(record: Dict[str, List[str]], tag: str, value: str) -> None:
    field = FIELD_MAP.get(tag, f"tag_{tag}")
    value = clean_text(value)
    if value:
        record.setdefault(field, []).append(value)


def parse_enw(path: Path) -> List[Dict[str, List[str]]]:
    records: List[Dict[str, List[str]]] = []
    current: Dict[str, List[str]] = {}
    last_field = ""

    with path.open("r", encoding="utf-8-sig", errors="replace") as file:
        for raw_line in file:
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                if current:
                    records.append(current)
                    current = {}
                    last_field = ""
                continue

            match = TAG_RE.match(line)
            if match:
                tag, value = match.groups()
                append_value(current, tag, value)
                last_field = FIELD_MAP.get(tag, f"tag_{tag}")
                continue

            # EndNote exports can wrap long field values onto following lines.
            if last_field and current.get(last_field):
                current[last_field][-1] = clean_text(current[last_field][-1] + " " + line)

    if current:
        records.append(current)
    return records


def unique(values: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for value in values:
        text = clean_text(value)
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def split_keywords(values: Iterable[str]) -> List[str]:
    parts: List[str] = []
    for value in values:
        for part in re.split(r"\s*;\s*|\s*,\s*", value):
            part = clean_text(part)
            if part:
                parts.append(part)
    return unique(parts)


def first(record: Dict[str, List[str]], field: str) -> str:
    values = record.get(field) or []
    return clean_text(values[0]) if values else ""


def parse_year(publication_date: str) -> str:
    match = re.search(r"(19|20)\d{2}", publication_date or "")
    return match.group(0) if match else ""


def flatten_record(record: Dict[str, List[str]], index: int, source: str, list_sep: str) -> Dict[str, str]:
    row = {column: "" for column in CSV_COLUMNS}
    row["source"] = source
    row["record_index"] = str(index)

    for field in FIELD_MAP.values():
        if field not in record:
            continue
        values = record[field]
        if field == "keywords":
            row[field] = list_sep.join(split_keywords(values))
        elif field in LIST_FIELDS:
            row[field] = list_sep.join(unique(values))
        else:
            row[field] = clean_text(" ".join(values))

    row["year"] = parse_year(row["publication_date"])
    row["venue"] = row["journal"] or row["booktitle"]

    extra = {
        key: values
        for key, values in sorted(record.items())
        if key.startswith("tag_") and values
    }
    row["extra_fields"] = json.dumps(extra, ensure_ascii=False) if extra else ""
    return row


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert EndNote .enw files to CSV.")
    parser.add_argument("input", nargs="?", default="acm.enw", help="Input .enw file. Default: acm.enw")
    parser.add_argument("-o", "--output", default="", help="Output .csv file. Default: input filename with .csv suffix")
    parser.add_argument("--source", default="", help="Value for the source column. Default: input file stem")
    parser.add_argument("--list-sep", default="; ", help="Separator for repeated fields. Default: '; '")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".csv")
    source = args.source or input_path.stem

    records = parse_enw(input_path)
    rows = [
        flatten_record(record, index=index, source=source, list_sep=args.list_sep)
        for index, record in enumerate(records, start=1)
    ]
    write_csv(output_path, rows)
    print(f"wrote {len(rows)} records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
