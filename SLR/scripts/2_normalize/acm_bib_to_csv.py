#!/usr/bin/env python3
"""Convert one or more BibTeX files to a single CSV.

The CSV keeps every BibTeX attribute found in the input files. By default it
keeps every input entry as a row. Use --dedupe to merge duplicate papers by DOI,
citation key, or title while preserving differing field values.

Usage:
  python3 acm_bib_to_csv.py acm.bib acm2.bib -o acm_bib_merged.csv
  python3 acm_bib_to_csv.py acm.bib acm2.bib -o acm_bib_merged.csv --dedupe
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


Record = Dict[str, str]

SPACE_RE = re.compile(r"\s+")
ENTRY_TYPE_RE = re.compile(r"[A-Za-z]+")
FIELD_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*")
PREFERRED_COLUMNS = [
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
]


def clean_text(value: str) -> str:
    return SPACE_RE.sub(" ", value or "").strip()


def find_matching_delimiter(text: str, start: int, open_char: str, close_char: str) -> int:
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unclosed BibTeX entry starting at position {start}")


def split_key_and_body(content: str) -> Tuple[str, str]:
    depth = 0
    in_quote = False
    escaped = False
    for index, char in enumerate(content):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_quote = not in_quote
            continue
        if in_quote:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "," and depth == 0:
            return content[:index].strip(), content[index + 1 :]
    return content.strip(), ""


def parse_braced_value(text: str, start: int) -> Tuple[str, int]:
    end = find_matching_delimiter(text, start, "{", "}")
    return text[start + 1 : end], end + 1


def parse_quoted_value(text: str, start: int) -> Tuple[str, int]:
    depth = 0
    escaped = False
    chars: List[str] = []
    index = start + 1
    while index < len(text):
        char = text[index]
        if escaped:
            chars.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            chars.append(char)
            escaped = True
            index += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        elif char == '"' and depth == 0:
            return "".join(chars), index + 1
        chars.append(char)
        index += 1
    return "".join(chars), index


def parse_bare_value(text: str, start: int) -> Tuple[str, int]:
    depth = 0
    in_quote = False
    escaped = False
    index = start
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if char == '"':
            in_quote = not in_quote
            index += 1
            continue
        if not in_quote:
            if char == "{":
                depth += 1
            elif char == "}":
                depth = max(0, depth - 1)
            elif char == "," and depth == 0:
                break
        index += 1
    return text[start:index].strip(), index


def parse_fields(body: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    index = 0
    while index < len(body):
        while index < len(body) and body[index] in " \t\r\n,":
            index += 1
        match = FIELD_NAME_RE.match(body, index)
        if not match:
            break

        name = match.group(0).lower()
        index = match.end()
        while index < len(body) and body[index].isspace():
            index += 1
        if index >= len(body) or body[index] != "=":
            break
        index += 1
        while index < len(body) and body[index].isspace():
            index += 1
        if index >= len(body):
            break

        if body[index] == "{":
            value, index = parse_braced_value(body, index)
        elif body[index] == '"':
            value, index = parse_quoted_value(body, index)
        else:
            value, index = parse_bare_value(body, index)

        value = clean_text(value.rstrip(","))
        if value:
            if name in fields and fields[name] != value:
                fields[name] = merge_values([fields[name], value])
            else:
                fields[name] = value
    return fields


def parse_bib_file(path: Path) -> List[Record]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    records: List[Record] = []
    index = 0
    source_index = 1

    while index < len(text):
        at = text.find("@", index)
        if at == -1:
            break
        type_match = ENTRY_TYPE_RE.match(text, at + 1)
        if not type_match:
            index = at + 1
            continue

        entry_type = type_match.group(0).lower()
        cursor = type_match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] not in "{(":
            index = cursor
            continue

        open_char = text[cursor]
        close_char = "}" if open_char == "{" else ")"
        end = find_matching_delimiter(text, cursor, open_char, close_char)
        content = text[cursor + 1 : end]
        citation_key, body = split_key_and_body(content)

        if entry_type not in {"comment", "preamble", "string"} and citation_key:
            record: Record = {
                "source_file": path.name,
                "source_index": str(source_index),
                "entry_type": entry_type,
                "citation_key": clean_text(citation_key),
            }
            record.update(parse_fields(body))
            records.append(record)
            source_index += 1

        index = end + 1

    return records


def merge_values(values: Iterable[str], sep: str = " || ") -> str:
    seen = set()
    output = []
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            output.append(text)
    return sep.join(output)


def dedupe_key(record: Record) -> str:
    doi = clean_text(record.get("doi", "")).lower()
    if doi:
        return "doi:" + doi
    citation_key = clean_text(record.get("citation_key", "")).lower()
    if citation_key:
        return "key:" + citation_key
    title = clean_text(record.get("title", "")).lower()
    year = clean_text(record.get("year", ""))
    return f"title:{title}|{year}"


def merge_duplicate_records(records: Iterable[Record]) -> List[Record]:
    merged: Dict[str, Record] = {}
    for record in records:
        key = dedupe_key(record)
        if key not in merged:
            merged[key] = dict(record)
            continue
        existing = merged[key]
        for field, value in record.items():
            if not value:
                continue
            if field not in existing or not existing[field]:
                existing[field] = value
            elif existing[field] != value:
                existing[field] = merge_values([existing[field], value])
    return list(merged.values())


def collect_columns(records: Iterable[Record]) -> List[str]:
    fields = set()
    for record in records:
        fields.update(record.keys())
    preferred = [column for column in PREFERRED_COLUMNS if column in fields]
    rest = sorted(fields.difference(preferred))
    return preferred + rest


def write_csv(path: Path, records: List[Record], columns: List[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({column: record.get(column, "") for column in columns})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge BibTeX files into one CSV while keeping all fields.")
    parser.add_argument("inputs", nargs="+", help="Input .bib files")
    parser.add_argument("-o", "--output", default="acm_bib_merged.csv", help="Output CSV path")
    parser.add_argument("--dedupe", action="store_true", help="Merge duplicate papers by DOI, citation key, or title/year")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records: List[Record] = []

    for value in args.inputs:
        path = Path(value)
        file_records = parse_bib_file(path)
        print(f"{path}: {len(file_records)} records", file=sys.stderr)
        records.extend(file_records)

    before = len(records)
    if args.dedupe:
        records = merge_duplicate_records(records)

    columns = collect_columns(records)
    write_csv(Path(args.output), records, columns)
    print(f"wrote {len(records)} records to {args.output}")
    if args.dedupe:
        print(f"deduped {before} input records to {len(records)} unique records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
