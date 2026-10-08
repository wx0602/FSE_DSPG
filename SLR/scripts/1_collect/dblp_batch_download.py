#!/usr/bin/env python3
"""Batch-download DBLP metadata for keywords listed in dblp_keywords.yml."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from dblp_download import API_URL, OUTPUT_COLUMNS, download, write_jsonl


BATCH_COLUMNS = OUTPUT_COLUMNS + [
    "dblp_search_query",
    "dblp_search_query_index",
    "dblp_query_total",
    "dblp_search_queries",
    "dblp_query_records",
    "dblp_match_count",
]


def clean_yaml_value(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value[0] in {"'", '"'} and value[-1:] == value[0]:
        value = value[1:-1]
    return value.strip()


def read_keywords(path: Path) -> list[str]:
    """Read a simple YAML file and collect all top-level list items.

    This intentionally avoids a PyYAML dependency. It supports the current
    format:

      keywords:
        - "program repair"
        - "security patch"
    """

    keywords: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            value = clean_yaml_value(stripped[2:])
            if value:
                keywords.append(value)

    return dedupe_keywords(keywords)


def dedupe_keywords(keywords: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for keyword in keywords:
        key = re.sub(r"\s+", " ", keyword).strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(keyword)
    return unique


def slugify(value: str, max_length: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.lower()).strip("_")
    return (slug[:max_length].strip("_") or "query")


def normalize_title(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def normalize_doi(value: str) -> str:
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value or "", flags=re.IGNORECASE)
    value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    return value.strip().lower()


def dedupe_key(row: Dict[str, str]) -> str:
    doi = normalize_doi(row.get("doi", ""))
    if doi:
        return f"doi:{doi}"

    title = normalize_title(row.get("title", ""))
    if title:
        return f"title:{title}"

    dblp_key = row.get("dblp_key") or row.get("citation_key")
    if dblp_key:
        return f"dblp:{dblp_key}"

    return f"row:{row.get('dblp_search_query', '')}:{row.get('source_index', '')}"


def append_unique(existing: str, value: str, sep: str = " || ") -> str:
    value = (value or "").strip()
    if not value:
        return existing

    parts = [part.strip() for part in existing.split(sep) if part.strip()]
    if value not in parts:
        parts.append(value)
    return sep.join(parts)


def merge_row(existing: Dict[str, str], row: Dict[str, str]) -> None:
    combine_fields = {
        "source_file",
        "note",
        "dblp_search_query",
        "dblp_search_queries",
        "dblp_query_records",
    }

    for field in BATCH_COLUMNS:
        value = row.get(field, "")
        if not value:
            continue
        if field in combine_fields:
            existing[field] = append_unique(existing.get(field, ""), value)
        elif not existing.get(field):
            existing[field] = value

    try:
        existing["dblp_match_count"] = str(int(existing.get("dblp_match_count", "1")) + 1)
    except ValueError:
        existing["dblp_match_count"] = "2"


def dedupe_rows(rows: Sequence[Dict[str, str]]) -> list[Dict[str, str]]:
    merged: OrderedDict[str, Dict[str, str]] = OrderedDict()
    for row in rows:
        key = dedupe_key(row)
        if key not in merged:
            merged[key] = {field: row.get(field, "") for field in BATCH_COLUMNS}
            merged[key]["dblp_match_count"] = "1"
        else:
            merge_row(merged[key], row)
    return list(merged.values())


def write_csv(path: Path, rows: Sequence[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BATCH_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_merged_outputs(merged_output: str, dedup_output: str, rows: Sequence[Dict[str, str]]) -> tuple[int, int]:
    deduped_rows = dedupe_rows(rows)
    write_csv(Path(merged_output), rows)
    write_csv(Path(dedup_output), deduped_rows)
    return len(rows), len(deduped_rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch-download DBLP metadata for YAML keyword queries.")
    parser.add_argument("--keywords", default="dblp_keywords.yml", help="YAML keyword file.")
    parser.add_argument("--out-dir", default="dblp", help="Directory for per-keyword outputs.")
    parser.add_argument("--limit", type=int, default=1000, help="Max records per keyword. Default: 1000.")
    parser.add_argument("--batch-size", type=int, default=100, help="DBLP API h parameter per request. Max: 1000. Default: 100.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument("--retries", type=int, default=3, help="HTTP retry attempts.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between retries/pages.")
    parser.add_argument("--query-sleep", type=float, default=5.0, help="Sleep seconds between keyword queries.")
    parser.add_argument("--api-url", default=API_URL, help="DBLP publication search API URL.")
    parser.add_argument("--merged-output", default="dblp_all_paper.csv", help="Merged raw output CSV.")
    parser.add_argument("--dedup-output", default="dblp_all_paper_dedup.csv", help="Merged deduplicated output CSV.")
    parser.add_argument("--no-jsonl", action="store_true", help="Do not write per-keyword raw JSONL files.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    keyword_path = Path(args.keywords)
    if not keyword_path.exists():
        raise SystemExit(f"keyword file not found: {keyword_path}")

    keywords = read_keywords(keyword_path)
    if not keywords:
        raise SystemExit(f"no keywords found in {keyword_path}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[Dict[str, str]] = []
    print(f"keywords: {len(keywords)}", file=sys.stderr)

    for query_index, keyword in enumerate(keywords, start=1):
        print(f"[{query_index}/{len(keywords)}] {keyword}", file=sys.stderr)
        rows, raw_hits, total = download(
            query=keyword,
            limit=args.limit,
            batch_size=args.batch_size,
            retries=args.retries,
            timeout=args.timeout,
            sleep_seconds=args.sleep,
            api_url=args.api_url,
        )

        for row in rows:
            row["dblp_search_query"] = keyword
            row["dblp_search_query_index"] = str(query_index)
            row["dblp_query_total"] = str(total or "")
            row["dblp_search_queries"] = keyword
            row["dblp_query_records"] = f"{keyword}#{row.get('dblp_rank', row.get('source_index', ''))}"
            row["dblp_match_count"] = "1"

        stem = f"{query_index:02d}_{slugify(keyword)}"
        csv_path = out_dir / f"{stem}.csv"
        jsonl_path = out_dir / f"{stem}.jsonl"
        write_csv(csv_path, rows)
        if not args.no_jsonl:
            write_jsonl(jsonl_path, raw_hits)

        all_rows.extend(rows)
        merged_count, deduped_count = write_merged_outputs(args.merged_output, args.dedup_output, all_rows)
        print(f"  total={total if total is not None else 'unknown'} downloaded={len(rows)} csv={csv_path}", file=sys.stderr)
        print(f"  checkpoint merged={merged_count} deduped={deduped_count}", file=sys.stderr)
        if query_index < len(keywords) and args.query_sleep > 0:
            time.sleep(args.query_sleep)

    merged_count, deduped_count = write_merged_outputs(args.merged_output, args.dedup_output, all_rows)

    print(f"merged rows: {merged_count}", file=sys.stderr)
    print(f"deduped rows: {deduped_count}", file=sys.stderr)
    print(args.merged_output)
    print(args.dedup_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
