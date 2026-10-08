#!/usr/bin/env python3
"""Collect recent paper metadata from ACM, SpringerLink, IEEE, and ScienceDirect.

Default scope is a year-level approximation of the last three years. For
example, running on 2026-06-11 searches publication years 2023-2026 unless
--from-year/--to-year is supplied.

API keys are read from environment variables:
  IEEE_API_KEY
  SPRINGER_API_KEY or SPRINGER_NATURE_API_KEY
  ELSEVIER_API_KEY
  CROSSREF_MAILTO, optional but recommended by Crossref

ACM Digital Library does not provide a generally available public search API, so
this script uses Crossref member metadata for ACM. Crossref is also used as a
fallback when an official source API key is not configured.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import sys
import time
from collections.abc import Iterable
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


Record = Dict[str, Any]

DEFAULT_SOURCES = ("acm", "springer", "ieee", "sciencedirect")
CROSSREF_MEMBERS = {
    "acm": "320",
    "springer": "297",
    "ieee": "263",
    "sciencedirect": "78",
}

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    text = html.unescape(str(value))
    text = TAG_RE.sub(" ", text)
    return SPACE_RE.sub(" ", text).strip()


def normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"[;,]\s*|\s+\|\s+", value)
        return [clean_text(part) for part in parts if clean_text(part)]
    if isinstance(value, dict):
        items: List[str] = []
        for child in value.values():
            items.extend(normalize_list(child))
        return items
    if isinstance(value, Iterable):
        items = []
        for child in value:
            if isinstance(child, dict):
                items.extend(normalize_list(child))
            else:
                text = clean_text(child)
                if text:
                    items.append(text)
        return items
    text = clean_text(value)
    return [text] if text else []


def unique_list(values: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for value in values:
        text = clean_text(value)
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def first(value: Any) -> str:
    if isinstance(value, list):
        return clean_text(value[0]) if value else ""
    return clean_text(value)


def parse_year(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value if 1900 <= value <= date.today().year + 2 else None
    text = clean_text(value)
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    return int(match.group(0))


def crossref_date(item: Dict[str, Any]) -> Tuple[str, Optional[int]]:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = item.get(key, {}).get("date-parts")
        if parts and parts[0]:
            year = int(parts[0][0])
            date_text = "-".join(f"{int(part):02d}" for part in parts[0])
            return date_text, year
    return "", None


def doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def record_key(record: Record) -> str:
    doi = clean_text(record.get("doi")).lower()
    if doi:
        return f"doi:{doi}"
    title = SPACE_RE.sub(" ", clean_text(record.get("title")).lower())
    year = record.get("year") or ""
    return "title:" + hashlib.sha1(f"{title}|{year}".encode("utf-8")).hexdigest()


def in_year_range(record: Record, from_year: int, to_year: int, keep_unknown: bool) -> bool:
    year = parse_year(record.get("year")) or parse_year(record.get("publication_date"))
    if year is None:
        return keep_unknown
    record["year"] = year
    return from_year <= year <= to_year


def http_json(
    url: str,
    params: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    retries: int = 3,
    timeout: int = 30,
    sleep_seconds: float = 1.0,
) -> Dict[str, Any]:
    query = urlencode({key: value for key, value in params.items() if value is not None}, doseq=True)
    full_url = f"{url}?{query}" if query else url
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "paper-collection-script/1.0 (metadata research)",
    }
    request_headers.update(headers or {})

    last_error: Optional[Exception] = None
    for attempt in range(retries):
        request = Request(full_url, headers=request_headers)
        try:
            with urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset, errors="replace"))
        except HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else sleep_seconds * (2**attempt)
            time.sleep(delay)
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == retries - 1:
                raise RuntimeError(f"request failed for {url}: {exc}") from exc
            time.sleep(sleep_seconds * (2**attempt))
    raise RuntimeError(f"request failed for {url}: {last_error}")


class CrossrefClient:
    endpoint = "https://api.crossref.org/works"

    def __init__(self, mailto: str = "") -> None:
        self.mailto = mailto

    def search(
        self,
        source: str,
        keyword: str,
        from_year: int,
        to_year: int,
        page_size: int,
        max_pages: int,
        sleep_seconds: float,
    ) -> List[Record]:
        member = CROSSREF_MEMBERS[source]
        headers = {}
        if self.mailto:
            headers["User-Agent"] = f"paper-collection-script/1.0 (mailto:{self.mailto})"

        cursor = "*"
        records: List[Record] = []
        for _ in range(max_pages):
            params = {
                "query.bibliographic": keyword,
                "filter": ",".join(
                    [
                        f"from-pub-date:{from_year}-01-01",
                        f"until-pub-date:{to_year}-12-31",
                        f"member:{member}",
                    ]
                ),
                "rows": page_size,
                "cursor": cursor,
                "select": "DOI,URL,title,abstract,subject,container-title,publisher,issued,published-print,published-online,author,type",
            }
            data = http_json(self.endpoint, params, headers=headers, sleep_seconds=sleep_seconds)
            message = data.get("message", {})
            items = message.get("items", [])
            if not items:
                break
            for item in items:
                publication_date, year = crossref_date(item)
                doi = clean_text(item.get("DOI"))
                authors = []
                for author in item.get("author") or []:
                    name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
                    if name:
                        authors.append(name)
                records.append(
                    {
                        "source": source,
                        "source_api": "crossref",
                        "search_keyword": keyword,
                        "title": first(item.get("title")),
                        "keywords": unique_list(item.get("subject") or []),
                        "abstract": clean_text(item.get("abstract")),
                        "authors": unique_list(authors),
                        "year": year,
                        "publication_date": publication_date,
                        "venue": first(item.get("container-title")),
                        "publisher": clean_text(item.get("publisher")),
                        "doi": doi,
                        "url": clean_text(item.get("URL")) or doi_url(doi),
                    }
                )
            next_cursor = message.get("next-cursor")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
            time.sleep(sleep_seconds)
        return records


class SpringerClient:
    endpoint = "https://api.springernature.com/meta/v2/json"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        keyword: str,
        from_year: int,
        to_year: int,
        page_size: int,
        max_pages: int,
        sleep_seconds: float,
    ) -> List[Record]:
        records: List[Record] = []
        for year in range(from_year, to_year + 1):
            for page in range(max_pages):
                params = {
                    "q": f"{keyword} year:{year}",
                    "p": page_size,
                    "s": page * page_size + 1,
                    "api_key": self.api_key,
                }
                data = http_json(self.endpoint, params, sleep_seconds=sleep_seconds)
                items = data.get("records") or []
                if not items:
                    break
                for item in items:
                    doi = clean_text(item.get("doi"))
                    authors = []
                    for creator in item.get("creators") or []:
                        name = creator.get("creator") if isinstance(creator, dict) else creator
                        if name:
                            authors.append(str(name))
                    url = ""
                    urls = item.get("url") or []
                    if isinstance(urls, list) and urls:
                        html_urls = [u.get("value") for u in urls if isinstance(u, dict) and u.get("format") == "html"]
                        url = clean_text(html_urls[0] if html_urls else urls[0].get("value") if isinstance(urls[0], dict) else urls[0])
                    records.append(
                        {
                            "source": "springer",
                            "source_api": "springer_nature_metadata",
                            "search_keyword": keyword,
                            "title": clean_text(item.get("title")),
                            "keywords": unique_list(normalize_list(item.get("keyword"))),
                            "abstract": clean_text(item.get("abstract")),
                            "authors": unique_list(authors),
                            "year": parse_year(item.get("publicationDate")) or year,
                            "publication_date": clean_text(item.get("publicationDate")),
                            "venue": clean_text(item.get("publicationName")),
                            "publisher": "Springer Nature",
                            "doi": doi,
                            "url": url or doi_url(doi),
                        }
                    )
                time.sleep(sleep_seconds)
        return records


class IEEEClient:
    endpoint = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        keyword: str,
        from_year: int,
        to_year: int,
        page_size: int,
        max_pages: int,
        sleep_seconds: float,
    ) -> List[Record]:
        records: List[Record] = []
        for page in range(max_pages):
            params = {
                "apikey": self.api_key,
                "format": "json",
                "querytext": keyword,
                "start_year": from_year,
                "end_year": to_year,
                "max_records": page_size,
                "start_record": page * page_size + 1,
                "sort_field": "publication_year",
                "sort_order": "desc",
            }
            data = http_json(self.endpoint, params, sleep_seconds=sleep_seconds)
            items = data.get("articles") or []
            if not items:
                break
            for item in items:
                doi = clean_text(item.get("doi"))
                authors = []
                raw_authors = item.get("authors", {}).get("authors") if isinstance(item.get("authors"), dict) else []
                for author in raw_authors or []:
                    name = author.get("full_name") if isinstance(author, dict) else author
                    if name:
                        authors.append(str(name))
                keywords = []
                index_terms = item.get("index_terms") or {}
                if isinstance(index_terms, dict):
                    for term_group in index_terms.values():
                        keywords.extend(normalize_list(term_group))
                keywords.extend(normalize_list(item.get("author_terms")))
                records.append(
                    {
                        "source": "ieee",
                        "source_api": "ieee_xplore",
                        "search_keyword": keyword,
                        "title": clean_text(item.get("title")),
                        "keywords": unique_list(keywords),
                        "abstract": clean_text(item.get("abstract")),
                        "authors": unique_list(authors),
                        "year": parse_year(item.get("publication_year")) or parse_year(item.get("publication_date")),
                        "publication_date": clean_text(item.get("publication_date")),
                        "venue": clean_text(item.get("publication_title")),
                        "publisher": "IEEE",
                        "doi": doi,
                        "url": clean_text(item.get("html_url")) or doi_url(doi),
                    }
                )
            time.sleep(sleep_seconds)
        return records


class ScienceDirectClient:
    search_endpoint = "https://api.elsevier.com/content/search/sciencedirect"
    abstract_endpoint = "https://api.elsevier.com/content/abstract/doi"

    def __init__(self, api_key: str, enrich_abstracts: bool = True) -> None:
        self.api_key = api_key
        self.enrich_abstracts = enrich_abstracts

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        keyword: str,
        from_year: int,
        to_year: int,
        page_size: int,
        max_pages: int,
        sleep_seconds: float,
    ) -> List[Record]:
        headers = {"X-ELS-APIKey": self.api_key}
        records: List[Record] = []
        for page in range(max_pages):
            params = {
                "query": keyword,
                "date": f"{from_year}-{to_year}",
                "count": page_size,
                "start": page * page_size,
                "apiKey": self.api_key,
                "httpAccept": "application/json",
            }
            data = http_json(self.search_endpoint, params, headers=headers, sleep_seconds=sleep_seconds)
            search_results = data.get("search-results") or {}
            items = search_results.get("entry") or []
            if not items:
                break
            for item in items:
                doi = clean_text(item.get("prism:doi"))
                abstract = clean_text(item.get("dc:description"))
                keywords = normalize_list(item.get("authkeywords")) or normalize_list(item.get("openaccessArticle"))
                if self.enrich_abstracts and doi and not abstract:
                    abstract, extra_keywords = self.fetch_abstract_by_doi(doi, headers, sleep_seconds)
                    keywords.extend(extra_keywords)
                links = item.get("link") or []
                url = ""
                if isinstance(links, list):
                    for link in links:
                        if isinstance(link, dict) and link.get("@ref") in ("scidir", "full-text", "self"):
                            url = clean_text(link.get("@href"))
                            break
                records.append(
                    {
                        "source": "sciencedirect",
                        "source_api": "elsevier_sciencedirect",
                        "search_keyword": keyword,
                        "title": clean_text(item.get("dc:title")),
                        "keywords": unique_list(keywords),
                        "abstract": abstract,
                        "authors": unique_list(normalize_list(item.get("authors") or item.get("dc:creator"))),
                        "year": parse_year(item.get("prism:coverDate") or item.get("prism:coverDisplayDate")),
                        "publication_date": clean_text(item.get("prism:coverDate") or item.get("prism:coverDisplayDate")),
                        "venue": clean_text(item.get("prism:publicationName")),
                        "publisher": "Elsevier",
                        "doi": doi,
                        "url": url or doi_url(doi),
                    }
                )
            time.sleep(sleep_seconds)
        return records

    def fetch_abstract_by_doi(
        self,
        doi: str,
        headers: Dict[str, str],
        sleep_seconds: float,
    ) -> Tuple[str, List[str]]:
        try:
            data = http_json(
                f"{self.abstract_endpoint}/{quote(doi, safe='/')}",
                {"apiKey": self.api_key, "httpAccept": "application/json"},
                headers=headers,
                retries=2,
                sleep_seconds=sleep_seconds,
            )
        except Exception as exc:
            stderr(f"[warn] Elsevier abstract lookup failed for DOI {doi}: {exc}")
            return "", []

        response = data.get("abstracts-retrieval-response") or {}
        coredata = response.get("coredata") or {}
        abstract = clean_text(coredata.get("dc:description"))
        keywords = []
        authkeywords = response.get("authkeywords")
        if isinstance(authkeywords, dict):
            keywords.extend(normalize_list(authkeywords.get("author-keyword")))
        return abstract, unique_list(keywords)


def merge_records(records: Sequence[Record]) -> List[Record]:
    merged: Dict[str, Record] = {}
    for record in records:
        key = record_key(record)
        if key not in merged:
            record["search_keywords"] = unique_list([record.pop("search_keyword", "")])
            merged[key] = record
            continue

        existing = merged[key]
        existing["search_keywords"] = unique_list(existing.get("search_keywords", []) + [record.get("search_keyword", "")])
        for list_field in ("keywords", "authors"):
            existing[list_field] = unique_list(existing.get(list_field, []) + record.get(list_field, []))
        for field in ("abstract", "title", "venue", "publisher", "doi", "url", "publication_date", "year", "source_api"):
            if not existing.get(field) and record.get(field):
                existing[field] = record[field]
        if record.get("source") and record["source"] not in normalize_list(existing.get("source")):
            existing["source"] = "|".join(unique_list(normalize_list(existing.get("source")) + [record["source"]]))
    return list(merged.values())


def write_jsonl(path: str, records: Sequence[Record]) -> None:
    with open(path, "w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: str, records: Sequence[Record]) -> None:
    fields = [
        "source",
        "source_api",
        "search_keywords",
        "year",
        "publication_date",
        "title",
        "authors",
        "keywords",
        "abstract",
        "venue",
        "publisher",
        "doi",
        "url",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("search_keywords", "authors", "keywords"):
                row[field] = "; ".join(record.get(field) or [])
            writer.writerow(row)


def source_records(
    source: str,
    keyword: str,
    args: argparse.Namespace,
    crossref: CrossrefClient,
) -> List[Record]:
    from_year, to_year = args.from_year, args.to_year
    common = (keyword, from_year, to_year, args.page_size, args.max_pages, args.sleep)

    try:
        if source == "acm":
            return crossref.search("acm", *common)
        if source == "springer":
            client = SpringerClient(os.getenv("SPRINGER_API_KEY") or os.getenv("SPRINGER_NATURE_API_KEY") or "")
            if client.available:
                return client.search(*common)
        if source == "ieee":
            client = IEEEClient(os.getenv("IEEE_API_KEY", ""))
            if client.available:
                return client.search(*common)
        if source == "sciencedirect":
            client = ScienceDirectClient(os.getenv("ELSEVIER_API_KEY", ""), enrich_abstracts=not args.no_elsevier_enrich)
            if client.available:
                return client.search(*common)
    except Exception as exc:
        stderr(f"[warn] {source} query failed for keyword '{keyword}': {exc}")
        if args.no_crossref_fallback:
            return []

    if not args.no_crossref_fallback and source in CROSSREF_MEMBERS:
        stderr(f"[info] using Crossref fallback for {source}, keyword '{keyword}'")
        try:
            return crossref.search(source, *common)
        except Exception as exc:
            stderr(f"[warn] Crossref fallback failed for {source}, keyword '{keyword}': {exc}")
    return []


def parse_sources(value: str) -> List[str]:
    sources = [item.strip().lower() for item in value.split(",") if item.strip()]
    unknown = sorted(set(sources) - set(DEFAULT_SOURCES))
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown sources: {', '.join(unknown)}")
    return sources


def build_parser() -> argparse.ArgumentParser:
    today = date.today()
    parser = argparse.ArgumentParser(
        description="Collect recent paper title, keywords, and abstract metadata.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--keywords", nargs="+", default=["AVR", "APR"], help="Search keywords.")
    parser.add_argument("--sources", type=parse_sources, default=",".join(DEFAULT_SOURCES), help="Comma-separated source list.")
    parser.add_argument("--years", type=int, default=3, help="Look back this many years when --from-year is omitted.")
    parser.add_argument("--from-year", type=int, default=None, help="Start publication year.")
    parser.add_argument("--to-year", type=int, default=today.year, help="End publication year.")
    parser.add_argument("--page-size", type=int, default=25, help="Records requested per page.")
    parser.add_argument("--max-pages", type=int, default=2, help="Maximum pages per source/keyword query.")
    parser.add_argument("--sleep", type=float, default=0.5, help="Delay between API requests in seconds.")
    parser.add_argument("--out-prefix", default="", help="Output filename prefix. Defaults to papers_FROM_TO.")
    parser.add_argument("--keep-unknown-year", action="store_true", help="Keep records where publication year cannot be parsed.")
    parser.add_argument("--no-crossref-fallback", action="store_true", help="Disable Crossref fallback for missing/failed official APIs.")
    parser.add_argument("--no-elsevier-enrich", action="store_true", help="Do not call Elsevier abstract retrieval API for missing abstracts.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.from_year is None:
        args.from_year = args.to_year - args.years
    if args.from_year > args.to_year:
        parser.error("--from-year cannot be greater than --to-year")

    crossref = CrossrefClient(mailto=os.getenv("CROSSREF_MAILTO", ""))
    collected: List[Record] = []
    for source in args.sources:
        for keyword in args.keywords:
            stderr(f"[info] querying {source} for '{keyword}' ({args.from_year}-{args.to_year})")
            records = source_records(source, keyword, args, crossref)
            filtered = [
                record
                for record in records
                if record.get("title") and in_year_range(record, args.from_year, args.to_year, args.keep_unknown_year)
            ]
            stderr(f"[info] {source}/{keyword}: kept {len(filtered)} of {len(records)} records")
            collected.extend(filtered)

    merged = merge_records(collected)
    merged.sort(key=lambda item: (str(item.get("source", "")), -(int(item.get("year") or 0)), str(item.get("title", "")).lower()))

    prefix = args.out_prefix or f"papers_{args.from_year}_{args.to_year}"
    csv_path = f"{prefix}.csv"
    jsonl_path = f"{prefix}.jsonl"
    write_csv(csv_path, merged)
    write_jsonl(jsonl_path, merged)

    stderr(f"[done] wrote {len(merged)} unique records")
    print(csv_path)
    print(jsonl_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
