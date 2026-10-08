#!/usr/bin/env python3
"""Collect recent paper metadata with Selenium.

This crawler reads public search/detail pages from ACM Digital Library,
SpringerLink, IEEE Xplore, and ScienceDirect. It does not log in, bypass
paywalls, solve CAPTCHA, or extract full text. Publisher page structure changes
often, so keep --debug-html-dir output when selectors need adjustment.

Install:
  python3 -m pip install -r requirements.txt

Example:
  python3 collect_papers_selenium.py --keywords AVR APR --from-year 2023 --to-year 2026
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
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode, urljoin, urlparse, urlunparse


Record = Dict[str, Any]

DEFAULT_SOURCES = ("acm", "springer", "ieee", "sciencedirect")

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)


SOURCE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "acm": {
        "base": "https://dl.acm.org",
        "result_selectors": [
            "li.issue-item",
            ".issue-item",
            ".search__item",
            ".search-result__item",
            ".hlFld-Title",
        ],
        "title_selectors": [
            ".issue-item__title a",
            "h5.issue-item__title a",
            ".hlFld-Title a",
            "a[href*='/doi/']",
        ],
        "snippet_selectors": [
            ".issue-item__abstract",
            ".issue-item__content-right p",
            ".abstract",
        ],
        "year_selectors": [
            ".bookPubDate",
            ".issue-item__detail",
            ".dot-separator",
            ".issue-heading",
        ],
        "venue_selectors": [
            ".epub-section__title",
            ".issue-item__detail",
        ],
        "detail_abstract_selectors": [
            ".abstractSection",
            ".abstractInFull",
            "#abstract",
            "section[aria-labelledby='abstract']",
            ".article__body .abstract",
        ],
        "detail_keyword_selectors": [
            ".keywords-section a",
            ".article__keywords a",
            ".keywords a",
            ".loa__item a",
            "a[href*='keyword']",
        ],
    },
    "springer": {
        "base": "https://link.springer.com",
        "result_selectors": [
            "li[data-test='search-result']",
            "li.app-card-open",
            ".app-card-open",
            ".c-card-open",
            ".c-card",
        ],
        "title_selectors": [
            "a[data-test='title']",
            "h3 a",
            "h2 a",
            ".c-card__title a",
            "a[href*='/article/']",
            "a[href*='/chapter/']",
        ],
        "snippet_selectors": [
            "[data-test='description']",
            ".c-card__summary",
            ".app-card-open__description",
            "p",
        ],
        "year_selectors": [
            "[data-test='published']",
            ".c-meta__item",
            ".c-card__meta",
            "time",
        ],
        "venue_selectors": [
            "[data-test='journal-title']",
            ".c-meta__item",
            ".c-card__meta",
        ],
        "detail_abstract_selectors": [
            "#Abs1-content",
            "[id^='Abs'][id$='-content']",
            "section[data-title='Abstract']",
            ".c-article-section__content",
            ".Abstract",
        ],
        "detail_keyword_selectors": [
            ".c-article-subject-list a",
            ".c-article-keywords a",
            ".KeywordGroup a",
            "[data-test='keyword']",
            "a[href*='keyword']",
        ],
    },
    "ieee": {
        "base": "https://ieeexplore.ieee.org",
        "result_selectors": [
            ".List-results-items",
            ".result-item",
            "xpl-results-item",
            ".results-item",
            "div[class*='result']",
        ],
        "title_selectors": [
            "h2 a",
            "h3 a",
            ".result-item-title a",
            ".document-title a",
            "a[href*='/document/']",
        ],
        "snippet_selectors": [
            ".description",
            ".abstract",
            "xpl-highlight",
            "p",
        ],
        "year_selectors": [
            ".publisher-info-container",
            ".description",
            ".stats-document-abstract-publishedIn",
            ".publication-year",
        ],
        "venue_selectors": [
            ".publisher-info-container",
            ".stats-document-abstract-publishedIn",
            ".publication-title",
        ],
        "detail_abstract_selectors": [
            "xpl-document-abstract",
            ".abstract-text",
            "div.abstract-text",
            ".document-abstract",
            ".u-mb-1",
        ],
        "detail_keyword_selectors": [
            "xpl-document-keyword-list a",
            ".doc-keywords-list .doc-keywords-list-item",
            ".document-keywords a",
            ".stats-keywords-list li",
            "a[href*='keywords']",
        ],
    },
    "sciencedirect": {
        "base": "https://www.sciencedirect.com",
        "result_selectors": [
            "li.ResultItem",
            "li.result-item",
            ".ResultItem",
            ".result-list-item",
            "ol.SearchResults li",
        ],
        "title_selectors": [
            "a.result-list-title-link",
            "h2 a",
            "h3 a",
            ".result-list-title a",
            "a[href*='/science/article/']",
        ],
        "snippet_selectors": [
            ".abstract",
            ".result-list-content",
            ".SubType",
            "p",
        ],
        "year_selectors": [
            ".SubType",
            ".srctitle-date-fields",
            ".publication-volume",
            "span",
        ],
        "venue_selectors": [
            ".srctitle-date-fields",
            ".publication-title",
            ".SubType",
        ],
        "detail_abstract_selectors": [
            "#abs0010",
            "section.Abstracts",
            ".abstract",
            ".Abstracts",
            ".abstract.author",
        ],
        "detail_keyword_selectors": [
            ".keywords-section button",
            ".keywords-section span",
            ".Keywords .keyword",
            ".keyword span",
            "[class*='Keywords'] a",
        ],
    },
}


META_FIELDS = {
    "title": ["citation_title", "dc.title", "dc.Title", "og:title"],
    "abstract": ["description", "og:description", "dc.description", "dc.Description"],
    "authors": ["citation_author", "dc.creator", "dc.Creator"],
    "keywords": ["citation_keywords", "keywords", "dc.subject", "dc.Subject"],
    "doi": ["citation_doi", "dc.identifier", "dc.Identifier", "prism.doi"],
    "publication_date": [
        "citation_publication_date",
        "citation_online_date",
        "citation_date",
        "dc.date",
        "dc.Date",
        "prism.publicationDate",
        "article:published_time",
    ],
    "venue": ["citation_journal_title", "citation_conference_title", "prism.publicationName"],
}


ABSTRACT_XPATHS = [
    "//*[self::section or self::div][.//*[self::h1 or self::h2 or self::h3][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')]][1]",
    "//*[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')][1]",
]


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


def strip_section_label(text: str, label: str) -> str:
    text = clean_text(text)
    text = re.sub(rf"^{label}\s*[:：]?\s*", "", text, flags=re.IGNORECASE)
    return clean_text(text)


def clean_abstract(text: str) -> str:
    text = strip_section_label(text, "abstract")
    text = re.split(r"\bKeywords?\b\s*[:：]?", text, maxsplit=1, flags=re.IGNORECASE)[0]
    return clean_text(text)


def split_keywords(values: Any) -> List[str]:
    raw_values = normalize_list(values)
    output: List[str] = []
    for value in raw_values:
        value = re.sub(r"^(author )?(keywords?|index terms)\s*[:：]\s*", "", value, flags=re.IGNORECASE)
        for part in re.split(r"[;\n•·]+|,\s*", value):
            part = clean_text(part)
            if not part or len(part) > 100:
                continue
            if part.lower() in {"keywords", "keyword", "index terms", "view pdf", "download pdf"}:
                continue
            output.append(part)
    return unique_list(output)


def normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [clean_text(value)] if clean_text(value) else []
    if isinstance(value, dict):
        items: List[str] = []
        for child in value.values():
            items.extend(normalize_list(child))
        return items
    if isinstance(value, Iterable):
        items = []
        for child in value:
            items.extend(normalize_list(child))
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


def parse_year(value: Any) -> Optional[int]:
    text = clean_text(value)
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    year = int(match.group(0))
    return year if 1900 <= year <= date.today().year + 2 else None


def extract_doi(text: str) -> str:
    match = DOI_RE.search(text or "")
    if not match:
        return ""
    return match.group(0).rstrip(".,);]")


def record_key(record: Record) -> str:
    doi = clean_text(record.get("doi")).lower()
    if doi:
        return f"doi:{doi}"
    url = canonical_url(clean_text(record.get("url")))
    if url:
        return f"url:{url}"
    title = SPACE_RE.sub(" ", clean_text(record.get("title")).lower())
    year = record.get("year") or ""
    return "title:" + hashlib.sha1(f"{title}|{year}".encode("utf-8")).hexdigest()


def canonical_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def in_year_range(record: Record, from_year: int, to_year: int, keep_unknown: bool) -> bool:
    year = parse_year(record.get("year")) or parse_year(record.get("publication_date"))
    if year is None:
        return keep_unknown
    record["year"] = year
    return from_year <= year <= to_year


def maybe_in_range_before_detail(record: Record, from_year: int, to_year: int) -> bool:
    year = parse_year(record.get("year")) or parse_year(record.get("publication_date"))
    return year is None or from_year <= year <= to_year


def import_selenium() -> Dict[str, Any]:
    try:
        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException, WebDriverException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: selenium. Install it with:\n"
            "  python3 -m pip install -r requirements.txt"
        ) from exc
    return {
        "webdriver": webdriver,
        "By": By,
        "WebDriverWait": WebDriverWait,
        "TimeoutException": TimeoutException,
        "WebDriverException": WebDriverException,
    }


def build_driver(args: argparse.Namespace) -> Any:
    selenium = import_selenium()
    webdriver = selenium["webdriver"]

    if args.browser == "firefox":
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service

        options = Options()
        if args.headless:
            options.add_argument("-headless")
        if args.binary:
            options.binary_location = args.binary
        service = Service(executable_path=args.driver_path) if args.driver_path else Service()
        driver = webdriver.Firefox(service=service, options=options)
    else:
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        options = Options()
        if args.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1100")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        if args.binary:
            options.binary_location = args.binary
        service = Service(executable_path=args.driver_path) if args.driver_path else Service()
        driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(args.page_timeout)
    return driver


def wait_for_page(driver: Any, timeout: int) -> None:
    selenium = import_selenium()
    wait = selenium["WebDriverWait"](driver, timeout)
    try:
        wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))
    except selenium["TimeoutException"]:
        stderr("[warn] page readiness wait timed out; continuing with current DOM")


def load_page(driver: Any, url: str, args: argparse.Namespace) -> bool:
    selenium = import_selenium()
    try:
        driver.get(url)
    except selenium["TimeoutException"]:
        stderr(f"[warn] page load timed out: {url}")
    except selenium["WebDriverException"] as exc:
        stderr(f"[warn] browser failed to load {url}: {exc}")
        return False

    wait_for_page(driver, args.wait)
    time.sleep(args.delay)
    if not args.no_cookie_click:
        click_cookie_buttons(driver)
    scroll_page(driver, args.scrolls, args.scroll_pause)
    return True


def wait_for_search_results(driver: Any, source: str, timeout: int) -> None:
    if source != "ieee":
        return

    selenium = import_selenium()
    selectors = SOURCE_CONFIGS[source]["result_selectors"] + SOURCE_CONFIGS[source]["title_selectors"]
    script = """
    const selectors = arguments[0];
    const hasResult = selectors.some((selector) => document.querySelector(selector));
    const body = document.body ? document.body.innerText : '';
    const isLoading = /Getting results\\.\\.\\./i.test(body);
    const hasNoResults = /No results|0 results|There are no results/i.test(body);
    return hasResult || hasNoResults || !isLoading;
    """
    try:
        selenium["WebDriverWait"](driver, timeout).until(lambda d: d.execute_script(script, selectors))
    except selenium["TimeoutException"]:
        stderr("[warn] search results wait timed out; continuing with current DOM")


def click_cookie_buttons(driver: Any) -> None:
    script = """
    const labels = [/^accept all$/i, /^accept$/i, /agree/i, /allow all/i, /同意/, /接受/];
    const nodes = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'));
    for (const node of nodes) {
      const text = (node.innerText || node.value || node.getAttribute('aria-label') || '').trim();
      if (!text || !labels.some((rx) => rx.test(text))) continue;
      const rect = node.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      node.click();
      return true;
    }
    return false;
    """
    try:
        if driver.execute_script(script):
            time.sleep(0.5)
    except Exception:
        return


def scroll_page(driver: Any, scrolls: int, pause: float) -> None:
    for _ in range(max(0, scrolls)):
        try:
            driver.execute_script("window.scrollBy(0, Math.floor(window.innerHeight * 0.85));")
        except Exception:
            return
        time.sleep(pause)
    try:
        driver.execute_script("window.scrollTo(0, 0);")
    except Exception:
        return


def page_blocked(driver: Any) -> bool:
    try:
        body = clean_text(
            driver.execute_script(
                "return [document.title || '', document.body ? document.body.innerText : '', document.documentElement ? document.documentElement.innerHTML.slice(0, 5000) : ''].join('\\n')"
            )
        ).lower()
    except Exception:
        return False
    markers = [
        "captcha",
        "challenge-platform",
        "client challenge",
        "cloudflare",
        "fastly",
        "access denied",
        "verify you are human",
        "security verification",
        "安全验证",
        "请稍候",
        "are you a robot",
        "unusual traffic",
        "temporarily blocked",
        "request blocked",
        "unable to load page",
        "oops, something went wrong",
        "there was a problem providing the content you requested",
    ]
    return any(marker in body for marker in markers)


def js_text_by_selectors(driver: Any, root: Any, selectors: Sequence[str]) -> str:
    script = """
    const root = arguments[0] || document;
    const selectors = arguments[1];
    for (const selector of selectors) {
      let el = null;
      try {
        el = root.querySelector(selector);
        if (!el && root.matches && root.matches(selector)) el = root;
      } catch (err) {
        continue;
      }
      if (!el) continue;
      const text = (el.innerText || el.textContent || el.getAttribute('content') || '').trim();
      if (text) return text;
    }
    return '';
    """
    try:
        return clean_text(driver.execute_script(script, root, list(selectors)))
    except Exception:
        return ""


def js_attr_by_selectors(driver: Any, root: Any, selectors: Sequence[str], attr: str) -> str:
    script = """
    const root = arguments[0] || document;
    const selectors = arguments[1];
    const attr = arguments[2];
    for (const selector of selectors) {
      let el = null;
      try {
        el = root.querySelector(selector);
        if (!el && root.matches && root.matches(selector)) el = root;
      } catch (err) {
        continue;
      }
      if (!el) continue;
      const value = attr === 'href' ? el.href : el.getAttribute(attr);
      if (value) return value;
    }
    return '';
    """
    try:
        return clean_text(driver.execute_script(script, root, list(selectors), attr))
    except Exception:
        return ""


def js_list_texts(driver: Any, root: Any, selectors: Sequence[str]) -> List[str]:
    script = """
    const root = arguments[0] || document;
    const selectors = arguments[1];
    const values = [];
    for (const selector of selectors) {
      let nodes = [];
      try {
        nodes = Array.from(root.querySelectorAll(selector));
        if (root.matches && root.matches(selector)) nodes.unshift(root);
      } catch (err) {
        continue;
      }
      for (const node of nodes) {
        const text = (node.innerText || node.textContent || node.getAttribute('content') || '').trim();
        if (text) values.push(text);
      }
      if (values.length) break;
    }
    return values;
    """
    try:
        return unique_list(clean_text(value) for value in driver.execute_script(script, root, list(selectors)))
    except Exception:
        return []


def css_elements(driver: Any, selectors: Sequence[str]) -> List[Any]:
    selenium = import_selenium()
    By = selenium["By"]
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            continue
        usable = []
        for element in elements:
            try:
                text = clean_text(element.text)
            except Exception:
                text = ""
            if text:
                usable.append(element)
        if usable:
            return usable
    return []


def xpath_text(driver: Any, xpaths: Sequence[str]) -> str:
    selenium = import_selenium()
    By = selenium["By"]
    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
        except Exception:
            continue
        for element in elements:
            try:
                text = clean_text(element.text)
            except Exception:
                text = ""
            if text:
                return text
    return ""


def meta_values(driver: Any, names: Sequence[str]) -> List[str]:
    script = """
    const wanted = new Set(arguments[0].map((item) => item.toLowerCase()));
    const values = [];
    for (const meta of document.querySelectorAll('meta')) {
      const key = (meta.getAttribute('name') || meta.getAttribute('property') || '').toLowerCase();
      if (!wanted.has(key)) continue;
      const content = (meta.getAttribute('content') || '').trim();
      if (content) values.push(content);
    }
    return values;
    """
    try:
        return unique_list(clean_text(value) for value in driver.execute_script(script, list(names)))
    except Exception:
        return []


def build_search_url(source: str, keyword: str, from_year: int, to_year: int, page: int, page_size: int) -> str:
    if source == "acm":
        params = {
            "AllField": keyword,
            "AfterYear": max(1900, from_year - 1),
            "BeforeYear": to_year + 1,
            "pageSize": page_size,
            "startPage": page,
        }
        return "https://dl.acm.org/action/doSearch?" + urlencode(params)
    if source == "springer":
        params = {
            "query": keyword,
            "facet-start-year": from_year,
            "facet-end-year": to_year,
            "page": page + 1,
        }
        return "https://link.springer.com/search?" + urlencode(params)
    if source == "ieee":
        params = {
            "queryText": keyword,
            "ranges": f"{from_year}_{to_year}_Year",
            "returnFacets": "ALL",
            "rowsPerPage": page_size,
            "pageNumber": page + 1,
        }
        return "https://ieeexplore.ieee.org/search/searchresult.jsp?" + urlencode(params)
    if source == "sciencedirect":
        params = {
            "qs": keyword,
            "date": f"{from_year}-{to_year}",
            "show": page_size,
            "offset": page * page_size,
        }
        return "https://www.sciencedirect.com/search?" + urlencode(params)
    raise ValueError(f"unknown source: {source}")


def extract_search_results(driver: Any, source: str, keyword: str) -> List[Record]:
    config = SOURCE_CONFIGS[source]
    elements = css_elements(driver, config["result_selectors"])
    if not elements:
        elements = css_elements(driver, config["title_selectors"])

    records: List[Record] = []
    seen = set()
    for element in elements:
        title = js_text_by_selectors(driver, element, config["title_selectors"])
        link = js_attr_by_selectors(driver, element, config["title_selectors"], "href")
        card_text = ""
        try:
            card_text = clean_text(element.text)
        except Exception:
            pass

        if not title and link:
            title = clean_text(card_text)
        if not title:
            continue

        link = urljoin(config["base"], link) if link else ""
        if len(title) < 4 or title.lower() in {"pdf", "html", "abstract"}:
            continue

        dedupe_key = canonical_url(link) or title.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        year_text = js_text_by_selectors(driver, element, config["year_selectors"]) or card_text
        snippet = js_text_by_selectors(driver, element, config["snippet_selectors"])
        venue = js_text_by_selectors(driver, element, config["venue_selectors"])
        doi = extract_doi(card_text) or extract_doi(link)

        records.append(
            {
                "source": source,
                "source_api": "selenium",
                "search_keyword": keyword,
                "title": title,
                "keywords": [],
                "abstract": clean_abstract(snippet),
                "authors": [],
                "year": parse_year(year_text),
                "publication_date": "",
                "venue": venue,
                "publisher": publisher_name(source),
                "doi": doi,
                "url": link,
            }
        )
    return records


def publisher_name(source: str) -> str:
    return {
        "acm": "ACM",
        "springer": "Springer Nature",
        "ieee": "IEEE",
        "sciencedirect": "Elsevier",
    }.get(source, source)


def extract_detail(driver: Any, source: str) -> Record:
    config = SOURCE_CONFIGS[source]
    metadata: Record = {}

    title_values = meta_values(driver, META_FIELDS["title"])
    if title_values:
        metadata["title"] = title_values[0]

    abstract = js_text_by_selectors(driver, None, config["detail_abstract_selectors"])
    if not abstract:
        abstract = xpath_text(driver, ABSTRACT_XPATHS)
    if not abstract:
        meta_abstract = meta_values(driver, META_FIELDS["abstract"])
        abstract = meta_abstract[0] if meta_abstract else ""
    if abstract:
        metadata["abstract"] = clean_abstract(abstract)

    keyword_values = js_list_texts(driver, None, config["detail_keyword_selectors"])
    keyword_values.extend(meta_values(driver, META_FIELDS["keywords"]))
    keywords = split_keywords(keyword_values)
    if keywords:
        metadata["keywords"] = keywords

    authors = meta_values(driver, META_FIELDS["authors"])
    if authors:
        metadata["authors"] = unique_list(authors)

    doi_values = meta_values(driver, META_FIELDS["doi"])
    doi = ""
    for value in doi_values:
        candidate = clean_text(value).replace("doi:", "").strip()
        doi = extract_doi(candidate)
        if not doi and DOI_RE.fullmatch(candidate):
            doi = candidate
        if doi:
            break
    if not doi:
        try:
            doi = extract_doi(driver.execute_script("return document.body ? document.body.innerText : ''"))
        except Exception:
            doi = ""
    if doi:
        metadata["doi"] = doi

    date_values = meta_values(driver, META_FIELDS["publication_date"])
    if date_values:
        metadata["publication_date"] = date_values[0]
        metadata["year"] = parse_year(date_values[0])

    venue_values = meta_values(driver, META_FIELDS["venue"])
    if venue_values:
        metadata["venue"] = venue_values[0]

    return metadata


def merge_detail(record: Record, detail: Record) -> Record:
    for field in ("keywords", "authors"):
        if detail.get(field):
            record[field] = unique_list(record.get(field, []) + detail.get(field, []))
    if detail.get("abstract") and len(clean_text(detail["abstract"])) > len(clean_text(record.get("abstract"))):
        record["abstract"] = detail["abstract"]
    if detail.get("title") and len(clean_text(detail["title"])) > len(clean_text(record.get("title"))):
        record["title"] = detail["title"]
    for field in ("title", "abstract", "year", "publication_date", "venue", "doi", "url"):
        if detail.get(field) and not record.get(field):
            record[field] = detail[field]
    return record


def fetch_details_for_records(
    driver: Any,
    records: List[Record],
    source: str,
    args: argparse.Namespace,
    detail_cache: Dict[str, Record],
) -> None:
    fetched = 0
    for index, record in enumerate(records, start=1):
        if fetched >= args.max_details_per_query:
            break
        url = clean_text(record.get("url"))
        if not url:
            continue
        cache_key = canonical_url(url)
        if cache_key in detail_cache:
            merge_detail(record, detail_cache[cache_key])
            continue

        stderr(f"[info] detail {source}: {index}/{len(records)} {url}")
        if not load_page(driver, url, args):
            continue
        if page_blocked(driver):
            stderr(f"[warn] blocked or verification page detected for detail URL: {url}")
            maybe_save_html(driver, args, source, record.get("search_keyword", ""), index, "blocked-detail")
            continue

        detail = extract_detail(driver, source)
        detail_cache[cache_key] = detail
        merge_detail(record, detail)
        fetched += 1
        time.sleep(args.delay)


def merge_records(records: Sequence[Record]) -> List[Record]:
    merged: Dict[str, Record] = {}
    for original in records:
        record = dict(original)
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


def parse_sources(value: str) -> List[str]:
    sources = [item.strip().lower() for item in value.split(",") if item.strip()]
    unknown = sorted(set(sources) - set(DEFAULT_SOURCES))
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown sources: {', '.join(unknown)}")
    return sources


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("_")[:120] or "page"


def maybe_save_html(
    driver: Any,
    args: argparse.Namespace,
    source: str,
    keyword: str,
    page: int,
    label: str,
) -> None:
    if not args.debug_html_dir:
        return
    os.makedirs(args.debug_html_dir, exist_ok=True)
    filename = safe_filename(f"{source}_{keyword}_{page}_{label}") + ".html"
    path = os.path.join(args.debug_html_dir, filename)
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(driver.page_source)
        stderr(f"[debug] saved HTML: {path}")
    except OSError as exc:
        stderr(f"[warn] failed to save debug HTML {path}: {exc}")


def build_parser() -> argparse.ArgumentParser:
    today = date.today()
    parser = argparse.ArgumentParser(
        description="Collect public paper metadata from publisher pages with Selenium.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--keywords", nargs="+", default=["AVR", "APR"], help="Search keywords.")
    parser.add_argument("--sources", type=parse_sources, default=",".join(DEFAULT_SOURCES), help="Comma-separated source list.")
    parser.add_argument("--years", type=int, default=3, help="Look back this many years when --from-year is omitted.")
    parser.add_argument("--from-year", type=int, default=None, help="Start publication year.")
    parser.add_argument("--to-year", type=int, default=today.year, help="End publication year.")
    parser.add_argument("--page-size", type=int, default=10, help="Search results requested per page when the site supports it.")
    parser.add_argument("--max-pages", type=int, default=2, help="Maximum search result pages per source/keyword.")
    parser.add_argument("--max-details-per-query", type=int, default=20, help="Maximum detail pages opened per source/keyword.")
    parser.add_argument("--out-prefix", default="", help="Output filename prefix. Defaults to selenium_papers_FROM_TO.")
    parser.add_argument("--keep-unknown-year", action="store_true", help="Keep records where publication year cannot be parsed.")
    parser.add_argument("--no-fetch-details", action="store_true", help="Only scrape search result pages, without opening detail pages.")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default="chrome", help="Browser used by Selenium.")
    parser.add_argument("--driver-path", default="", help="Optional explicit chromedriver/geckodriver path.")
    parser.add_argument("--binary", default="", help="Optional browser binary path.")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window instead of headless mode.")
    parser.add_argument("--wait", type=int, default=20, help="Seconds to wait for document readiness.")
    parser.add_argument("--page-timeout", type=int, default=45, help="Browser page load timeout in seconds.")
    parser.add_argument("--delay", type=float, default=2.0, help="Polite delay after page loads and between detail requests.")
    parser.add_argument("--scrolls", type=int, default=3, help="Scroll passes after loading a page to trigger lazy content.")
    parser.add_argument("--scroll-pause", type=float, default=0.7, help="Delay between scroll passes.")
    parser.add_argument("--no-cookie-click", action="store_true", help="Do not click common cookie consent buttons.")
    parser.add_argument("--debug-html-dir", default="", help="Directory for HTML snapshots when a page yields no results or is blocked.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.headless = not args.headed
    if args.from_year is None:
        args.from_year = args.to_year - args.years
    if args.from_year > args.to_year:
        parser.error("--from-year cannot be greater than --to-year")

    driver = build_driver(args)
    collected: List[Record] = []
    detail_cache: Dict[str, Record] = {}
    try:
        for source in args.sources:
            for keyword in args.keywords:
                query_records: List[Record] = []
                for page in range(args.max_pages):
                    url = build_search_url(source, keyword, args.from_year, args.to_year, page, args.page_size)
                    stderr(f"[info] search {source}/{keyword} page {page + 1}: {url}")
                    if not load_page(driver, url, args):
                        continue
                    wait_for_search_results(driver, source, args.wait)
                    if page_blocked(driver):
                        stderr(f"[warn] blocked or verification page detected: {source}/{keyword} page {page + 1}")
                        maybe_save_html(driver, args, source, keyword, page + 1, "blocked-search")
                        break
                    page_records = extract_search_results(driver, source, keyword)
                    page_records = [
                        record
                        for record in page_records
                        if record.get("title") and maybe_in_range_before_detail(record, args.from_year, args.to_year)
                    ]
                    stderr(f"[info] {source}/{keyword} page {page + 1}: found {len(page_records)} candidate records")
                    if not page_records:
                        maybe_save_html(driver, args, source, keyword, page + 1, "empty-search")
                        break
                    query_records.extend(page_records)
                    time.sleep(args.delay)

                query_records = merge_records(query_records)
                for record in query_records:
                    record["search_keyword"] = "; ".join(record.pop("search_keywords", []))

                if not args.no_fetch_details:
                    fetch_details_for_records(driver, query_records, source, args, detail_cache)

                kept = [
                    record
                    for record in query_records
                    if record.get("title") and in_year_range(record, args.from_year, args.to_year, args.keep_unknown_year)
                ]
                stderr(f"[info] {source}/{keyword}: kept {len(kept)} of {len(query_records)} records")
                collected.extend(kept)
    finally:
        driver.quit()

    merged = merge_records(collected)
    merged.sort(key=lambda item: (str(item.get("source", "")), -(int(item.get("year") or 0)), str(item.get("title", "")).lower()))

    prefix = args.out_prefix or f"selenium_papers_{args.from_year}_{args.to_year}"
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
