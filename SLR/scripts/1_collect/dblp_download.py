#!/usr/bin/env python3
"""Download publication metadata from the DBLP publication search API.

DBLP search API:
  https://dblp.org/search/publ/api?q=...&format=json&h=1000&f=0

The CSV output uses the same common columns as the existing ACM/IEEE/Springer
and ScienceDirect converters in this directory. DBLP usually does not provide
abstracts or keywords through this search API, so those fields are left empty.

Usage:
  python dblp_download.py "automated program repair"
  python dblp_download.py "automated vulnerability repair" -o dblp_avr.csv
  python dblp_download.py "security patch" --limit 1000 --jsonl dblp_security_patch.jsonl
"""

from __future__ import annotations

import argparse
import csv
import html
import http.client
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


Record = Dict[str, str]

API_URL = "https://dblp.org/search/publ/api"
MAX_BATCH_SIZE = 1000

COMMON_COLUMNS = [
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

DBLP_EXTRA_COLUMNS = [
    "dblp_rank",
    "dblp_score",
    "dblp_id",
    "dblp_key",
    "dblp_type",
    "dblp_venue",
    "dblp_ee",
]

OUTPUT_COLUMNS = COMMON_COLUMNS + DBLP_EXTRA_COLUMNS


def clean_text(value: Any) -> str:
    text = extract_text(value)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(clean_text(item) for item in value if clean_text(item))
    if isinstance(value, dict):
        if "text" in value:
            return extract_text(value["text"])
        if "#text" in value:
            return extract_text(value["#text"])
        return "; ".join(clean_text(item) for item in value.values() if clean_text(item))
    return str(value)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_doi(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def extract_authors(info: dict[str, Any]) -> str:
    authors = info.get("authors", {})
    if isinstance(authors, dict):
        values = authors.get("author", [])
    else:
        values = authors

    names = []
    for author in as_list(values):
        name = clean_text(author)
        if name:
            names.append(name)
    return " and ".join(names)


def first_nonempty(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def page_count(pages: str) -> str:
    parts = re.findall(r"\d+", pages or "")
    if len(parts) >= 2:
        start, end = int(parts[0]), int(parts[-1])
        if end >= start:
            return str(end - start + 1)
    if len(parts) == 1:
        return "1"
    return ""


def infer_venue_fields(info: dict[str, Any]) -> tuple[str, str, str]:
    venue = clean_text(info.get("venue", ""))
    pub_type = clean_text(info.get("type", "")).lower()

    if pub_type in {"journal articles", "article"}:
        return venue, "", ""

    if pub_type in {"conference and workshop papers", "conference", "inproceedings"}:
        return "", venue, venue

    return "", venue, venue


def build_api_url(query: str, offset: int, batch_size: int, api_url: str = API_URL) -> str:
    params = {
        "q": query,
        "format": "json",
        "h": str(batch_size),
        "f": str(offset),
        "c": "0",
    }
    return f"{api_url}?{urlencode(params)}"


def fetch_json_with_curl(url: str, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        ["curl", "-L", "--silent", "--show-error", "--max-time", str(timeout), url],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout + 5,
    )
    return json.loads(completed.stdout)


def fetch_json_with_urllib(request: Request, timeout: int) -> dict[str, Any]:
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_json(url: str, retries: int, timeout: int, sleep_seconds: float) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "paper-collection-dblp-downloader/1.0 (+https://dblp.org)",
            "Accept": "application/json",
            "Connection": "close",
        },
    )

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fetch_json_with_curl(url, timeout=timeout)
        except FileNotFoundError:
            try:
                return fetch_json_with_urllib(request, timeout=timeout)
            except (HTTPError, URLError, TimeoutError, http.client.RemoteDisconnected, json.JSONDecodeError) as error:
                last_error = error
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            last_error = error
        if attempt < retries:
            time.sleep(sleep_seconds * attempt)

    raise RuntimeError(f"failed to fetch DBLP API after {retries} attempts: {last_error}")


def get_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hits = payload.get("result", {}).get("hits", {}).get("hit", [])
    return [hit for hit in as_list(hits) if isinstance(hit, dict)]


def get_total(payload: dict[str, Any]) -> int | None:
    total = payload.get("result", {}).get("hits", {}).get("@total")
    try:
        return int(total)
    except (TypeError, ValueError):
        return None


def normalize_hit(hit: dict[str, Any], query: str, rank: int, api_url: str) -> Record:
    info = hit.get("info", {})
    if not isinstance(info, dict):
        info = {}

    journal, booktitle, series = infer_venue_fields(info)
    pages = clean_text(info.get("pages", ""))
    doi = normalize_doi(info.get("doi", ""))
    ee = clean_text(info.get("ee", ""))
    dblp_url = clean_text(info.get("url", ""))
    record_url = f"https://dblp.org/{dblp_url.lstrip('/')}" if dblp_url.startswith("rec/") else dblp_url

    row = {column: "" for column in OUTPUT_COLUMNS}
    row.update(
        {
            "source_file": api_url,
            "source_index": str(rank),
            "entry_type": clean_text(info.get("type", "")),
            "citation_key": clean_text(info.get("key", "")),
            "title": clean_text(info.get("title", "")),
            "author": extract_authors(info),
            "year": clean_text(info.get("year", "")),
            "journal": journal,
            "booktitle": booktitle,
            "series": series,
            "publisher": "DBLP",
            "doi": doi,
            "url": ee or record_url,
            "pages": pages,
            "numpages": page_count(pages),
            "dblp_rank": str(rank),
            "dblp_score": clean_text(hit.get("@score", "")),
            "dblp_id": clean_text(hit.get("@id", "")),
            "dblp_key": clean_text(info.get("key", "")),
            "dblp_type": clean_text(info.get("type", "")),
            "dblp_venue": clean_text(info.get("venue", "")),
            "dblp_ee": ee,
        }
    )

    if not row["note"]:
        row["note"] = f"dblp query: {query}"

    return row


def download(
    query: str,
    limit: int,
    batch_size: int,
    retries: int,
    timeout: int,
    sleep_seconds: float,
    api_url: str = API_URL,
) -> tuple[list[Record], list[dict[str, Any]], int | None]:
    rows: list[Record] = []
    raw_hits: list[dict[str, Any]] = []
    total: int | None = None
    offset = 0

    while len(rows) < limit:
        current_batch_size = min(batch_size, MAX_BATCH_SIZE)
        request_url = build_api_url(query, offset, current_batch_size, api_url=api_url)
        payload = fetch_json(request_url, retries=retries, timeout=timeout, sleep_seconds=sleep_seconds)
        if total is None:
            total = get_total(payload)

        hits = get_hits(payload)
        if not hits:
            break

        for hit in hits:
            rank = len(rows) + 1
            rows.append(normalize_hit(hit, query=query, rank=rank, api_url=request_url))
            raw_hits.append(hit)
            if len(rows) >= limit:
                break

        offset += len(hits)
        if total is not None and offset >= min(total, limit):
            break
        if total is None and len(hits) < current_batch_size:
            break
        if len(rows) < limit:
            time.sleep(sleep_seconds)

    return rows, raw_hits, total


def write_csv(path: Path, rows: Sequence[Record]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, hits: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for hit in hits:
            handle.write(json.dumps(hit, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download the first N DBLP publication search results for one keyword/query.")
    parser.add_argument("query", help="DBLP publication search keyword/query, e.g. 'automated program repair'.")
    parser.add_argument("-o", "--output", default="dblp_papers.csv", help="Output CSV path.")
    parser.add_argument("--jsonl", help="Optional output path for raw DBLP hit records as JSONL.")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum number of records to download. Default: 1000.")
    parser.add_argument("--batch-size", type=int, default=100, help="DBLP API h parameter per request. Max: 1000. Default: 100.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument("--retries", type=int, default=3, help="HTTP retry attempts.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between retries/pages.")
    parser.add_argument("--api-url", default=API_URL, help="DBLP publication search API URL.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")

    batch_size = min(args.batch_size, MAX_BATCH_SIZE)
    rows, raw_hits, total = download(
        query=args.query,
        limit=args.limit,
        batch_size=batch_size,
        retries=args.retries,
        timeout=args.timeout,
        sleep_seconds=args.sleep,
        api_url=args.api_url,
    )

    write_csv(Path(args.output), rows)
    if args.jsonl:
        write_jsonl(Path(args.jsonl), raw_hits)

    print(f"query: {args.query}", file=sys.stderr)
    if total is not None:
        print(f"dblp reported total hits: {total}", file=sys.stderr)
    print(f"downloaded records: {len(rows)}", file=sys.stderr)
    print(args.output)
    if args.jsonl:
        print(args.jsonl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
