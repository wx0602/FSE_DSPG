#!/usr/bin/env python3
"""Filter CCF-A long papers from a CSV exported from BibTeX.

The rule table is intentionally kept in this file so it can be reviewed and
edited when your local CCF catalogue changes. The default list focuses on
AI-related, software engineering/programming languages, and security venues.

Usage:
  python3 acm_filter_ccf_a_long_papers.py acm_bib_merged.csv
  python3 acm_filter_ccf_a_long_papers.py acm_bib_merged.csv -o acm_ccf_a_long_papers.csv --min-pages 8
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


Row = Dict[str, str]


@dataclass(frozen=True)
class VenueRule:
    area: str
    short: str
    kind: str
    aliases: Tuple[str, ...]
    negative_aliases: Tuple[str, ...] = ()


# Seed CCF-A rule table for the areas requested by the user. Keep aliases broad
# enough to match ACM/IEEE BibTeX exports, but use negative_aliases to avoid
# common false positives such as ASIA CCS or companion proceedings.
CCF_A_RULES: Tuple[VenueRule, ...] = (
    # AI / ML / data mining / IR / web / multimedia adjacent CCF-A venues.
    VenueRule(
        "ai",
        "AAAI",
        "conference",
        ("AAAI", "AAAI Conference on Artificial Intelligence"),
        ("AAAI/ACM Conference on AI, Ethics, and Society", "AIES"),
    ),
    VenueRule("ai", "IJCAI", "conference", ("IJCAI", "International Joint Conference on Artificial Intelligence")),
    VenueRule("ai", "NeurIPS", "conference", ("NeurIPS", "NIPS", "Neural Information Processing Systems")),
    VenueRule("ai", "ICML", "conference", ("ICML", "International Conference on Machine Learning")),
    VenueRule("ai", "ICLR", "conference", ("ICLR", "International Conference on Learning Representations")),
    VenueRule("ai", "KDD", "conference", ("KDD", "SIGKDD", "Knowledge Discovery and Data Mining")),
    VenueRule("ai", "SIGIR", "conference", ("SIGIR", "Research and Development in Information Retrieval")),
    VenueRule("ai", "WWW", "conference", ("WWW", "The Web Conference", "ACM Web Conference", "World Wide Web Conference")),
    VenueRule("ai", "ACL", "conference", ("ACL", "Annual Meeting of the Association for Computational Linguistics")),
    VenueRule("ai", "EMNLP", "conference", ("EMNLP", "Empirical Methods in Natural Language Processing")),
    VenueRule("ai", "CVPR", "conference", ("CVPR", "Computer Vision and Pattern Recognition")),
    VenueRule("ai", "ICCV", "conference", ("ICCV", "International Conference on Computer Vision")),
    VenueRule("ai", "ECCV", "conference", ("ECCV", "European Conference on Computer Vision")),
    VenueRule(
        "ai",
        "ACM MM",
        "conference",
        ("ACM MM", "ACM Multimedia", "ACM International Conference on Multimedia"),
        ("MMSys", "Multimedia Systems Conference", "ICMR", "International Conference on Multimedia Retrieval"),
    ),
    VenueRule("ai", "JMLR", "journal", ("J. Mach. Learn. Res.", "Journal of Machine Learning Research", "JMLR")),
    VenueRule("ai", "AIJ", "journal", ("Artificial Intelligence",)),
    VenueRule("ai", "TPAMI", "journal", ("IEEE Trans. Pattern Anal. Mach. Intell.", "TPAMI", "Pattern Analysis and Machine Intelligence")),
    # Software engineering / programming languages.
    VenueRule("se", "ICSE", "conference", ("ICSE", "International Conference on Software Engineering")),
    VenueRule("se", "FSE", "conference", ("FSE", "ESEC/FSE", "Foundations of Software Engineering")),
    VenueRule("se", "ASE", "conference", ("ASE", "Automated Software Engineering")),
    VenueRule("se", "ISSTA", "conference", ("ISSTA", "Software Testing and Analysis")),
    VenueRule("se", "PLDI", "conference", ("PLDI", "Programming Language Design and Implementation")),
    VenueRule("se", "POPL", "conference", ("POPL", "Principles of Programming Languages")),
    VenueRule("se", "OOPSLA", "conference", ("OOPSLA", "Object-Oriented Programming, Systems, Languages, and Applications")),
    VenueRule("se", "TOSEM", "journal", ("ACM Trans. Softw. Eng. Methodol.", "ACM Transactions on Software Engineering and Methodology", "TOSEM")),
    VenueRule("se", "TSE", "journal", ("IEEE Trans. Software Eng.", "IEEE Transactions on Software Engineering", "TSE")),
    VenueRule("se", "PACMSE", "journal", ("Proc. ACM Softw. Eng.", "Proceedings of the ACM on Software Engineering", "PACMSE")),
    VenueRule("se", "PACMPL", "journal", ("Proc. ACM Program. Lang.", "Proceedings of the ACM on Programming Languages", "PACMPL")),
    # Security and privacy.
    VenueRule(
        "security",
        "CCS",
        "conference",
        ("CCS", "ACM SIGSAC Conference on Computer and Communications Security", "Computer and Communications Security"),
        ("ASIA CCS", "Asia Conference on Computer and Communications Security", "ASIACCS"),
    ),
    VenueRule("security", "IEEE S&P", "conference", ("IEEE S&P", "IEEE Symposium on Security and Privacy", "Oakland")),
    VenueRule("security", "USENIX Security", "conference", ("USENIX Security", "USENIX Security Symposium")),
    VenueRule("security", "NDSS", "conference", ("NDSS", "Network and Distributed System Security Symposium")),
    VenueRule("security", "TOPS", "journal", ("ACM Trans. Priv. Secur.", "ACM Transactions on Privacy and Security", "TOPS")),
    VenueRule("security", "TDSC", "journal", ("IEEE Trans. Dependable Secure Comput.", "IEEE Transactions on Dependable and Secure Computing", "TDSC")),
    VenueRule("security", "TIFS", "journal", ("IEEE Trans. Inf. Forensics Security", "IEEE Transactions on Information Forensics and Security", "TIFS")),
)


NON_LONG_TERMS = (
    "companion",
    "workshop",
    "poster",
    "demo",
    "tutorial",
    "doctoral",
    "student research",
    "src",
    "extended abstract",
    "short paper",
    "late-breaking",
    "keynote",
    "panel",
    "industry",
    "industry track",
    "software engineering in practice",
    "seip",
    "symposium on doctoral symposium",
)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize(value: str) -> str:
    value = clean_text(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return clean_text(value)


def text_for_matching(row: Row) -> str:
    fields = ("series", "booktitle", "journal", "title")
    return " | ".join(clean_text(row.get(field, "")) for field in fields if row.get(field))


def abbreviation_match(alias: str, haystack: str) -> bool:
    alias_norm = normalize(alias)
    hay_norm = normalize(haystack)
    if not alias_norm:
        return False
    if len(alias_norm) <= 12 and " " not in alias_norm:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(alias_norm)}(?![a-z0-9])", hay_norm))
    return alias_norm in hay_norm


def match_rule(row: Row, rule: VenueRule) -> Optional[Tuple[str, str]]:
    haystack = text_for_matching(row)
    if any(abbreviation_match(alias, haystack) for alias in rule.negative_aliases):
        return None
    if rule.kind == "journal":
        fields = ("journal",)
    else:
        fields = ("series", "booktitle")
    for field in fields:
        value = clean_text(row.get(field, ""))
        if not value:
            continue
        if any(abbreviation_match(alias, value) for alias in rule.aliases):
            return field, value
    return None


def parse_pages(row: Row) -> Tuple[Optional[int], str]:
    numpages = clean_text(row.get("numpages", ""))
    if numpages:
        match = re.search(r"\d+", numpages)
        if match:
            return int(match.group(0)), "numpages"

    pages = clean_text(row.get("pages", ""))
    if pages:
        parts = re.findall(r"\d+", pages)
        if len(parts) >= 2:
            start, end = int(parts[0]), int(parts[-1])
            if end >= start:
                return end - start + 1, "pages"
        if len(parts) == 1:
            return 1, "pages-single"

    return None, "missing"


def non_long_reason(row: Row) -> str:
    entry_type = normalize(row.get("entry_type", ""))
    if entry_type in {"proceedings", "book"}:
        return f"entry_type={entry_type}"
    text = normalize(" ".join(row.get(field, "") for field in ("series", "booktitle", "title", "note")))
    for term in NON_LONG_TERMS:
        if normalize(term) in text:
            return f"non-main-track term: {term}"
    return ""


def is_long_paper(row: Row, rule: VenueRule, min_pages: int, include_journal_unknown_pages: bool) -> Tuple[bool, str, Optional[int]]:
    reason = non_long_reason(row)
    if reason:
        return False, reason, None

    entry_type = normalize(row.get("entry_type", ""))
    if entry_type not in {"article", "inproceedings", "inbook"}:
        return False, f"unsupported entry_type={entry_type or 'missing'}", None

    pages, page_source = parse_pages(row)
    if pages is not None and pages >= min_pages:
        return True, f"{page_source}={pages} >= {min_pages}", pages

    if (
        rule.kind == "journal"
        and entry_type == "article"
        and pages is None
        and include_journal_unknown_pages
    ):
        return True, "journal article with missing page count", pages

    if pages is None:
        return False, "missing page count", pages
    return False, f"{page_source}={pages} < {min_pages}", pages


def areas_from_arg(value: str) -> List[str]:
    areas = [item.strip().lower() for item in value.split(",") if item.strip()]
    allowed = {rule.area for rule in CCF_A_RULES}
    invalid = sorted(set(areas).difference(allowed))
    if invalid:
        raise SystemExit(f"unknown areas: {', '.join(invalid)}; allowed: {', '.join(sorted(allowed))}")
    return areas


def annotate_row(
    row: Row,
    rule: VenueRule,
    match_field: str,
    match_value: str,
    is_long: bool,
    long_reason: str,
    pages: Optional[int],
) -> Row:
    annotated = dict(row)
    annotated["ccf_rank"] = "A"
    annotated["ccf_area"] = rule.area
    annotated["ccf_venue"] = rule.short
    annotated["ccf_venue_kind"] = rule.kind
    annotated["ccf_match_field"] = match_field
    annotated["ccf_match_value"] = match_value
    annotated["paper_pages"] = "" if pages is None else str(pages)
    annotated["is_long_paper"] = "yes" if is_long else "no"
    annotated["long_paper_reason"] = long_reason
    return annotated


def unique_rows(rows: Iterable[Row]) -> List[Row]:
    seen = set()
    output = []
    for row in rows:
        doi = normalize(row.get("doi", ""))
        key = "doi:" + doi if doi else "key:" + normalize(row.get("citation_key", ""))
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def preferred_columns(input_columns: Sequence[str]) -> List[str]:
    metadata = [
        "ccf_rank",
        "ccf_area",
        "ccf_venue",
        "ccf_venue_kind",
        "ccf_match_field",
        "ccf_match_value",
        "paper_pages",
        "is_long_paper",
        "long_paper_reason",
    ]
    return metadata + [column for column in input_columns if column not in metadata]


def write_csv(path: Path, rows: Sequence[Row], columns: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def coverage_rows(rules: Sequence[VenueRule], candidates: Sequence[Row], selected: Sequence[Row]) -> List[Row]:
    rows = []
    for rule in rules:
        candidate_count = sum(1 for row in candidates if row.get("ccf_area") == rule.area and row.get("ccf_venue") == rule.short)
        selected_count = sum(1 for row in selected if row.get("ccf_area") == rule.area and row.get("ccf_venue") == rule.short)
        rows.append(
            {
                "ccf_area": rule.area,
                "ccf_rank": "A",
                "ccf_venue": rule.short,
                "ccf_venue_kind": rule.kind,
                "candidate_matches": str(candidate_count),
                "long_paper_matches": str(selected_count),
                "covered": "yes" if selected_count else "no",
                "aliases": "; ".join(rule.aliases),
            }
        )
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter CCF-A long papers and report venue coverage.")
    parser.add_argument("input", nargs="?", default="acm_bib_merged.csv", help="Input CSV. Default: acm_bib_merged.csv")
    parser.add_argument("-o", "--output", default="acm_ccf_a_long_papers.csv", help="Filtered long-paper CSV output.")
    parser.add_argument("--coverage-output", default="acm_ccf_a_coverage.csv", help="Coverage summary CSV output.")
    parser.add_argument("--excluded-output", default="acm_ccf_a_excluded_candidates.csv", help="Matched but excluded candidate CSV output.")
    parser.add_argument("--areas", default="ai,se,security", help="Comma-separated areas: ai,se,security.")
    parser.add_argument("--min-pages", type=int, default=8, help="Minimum page count for a conference long paper.")
    parser.add_argument(
        "--strict-pages",
        action="store_true",
        help="Require page count for journal articles too. By default CCF-A journal articles with missing page count are kept.",
    )
    parser.add_argument("--no-dedupe", action="store_true", help="Do not deduplicate matched rows by DOI/citation key.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    areas = set(areas_from_arg(args.areas))
    rules = [rule for rule in CCF_A_RULES if rule.area in areas]

    input_path = Path(args.input)
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        input_columns = reader.fieldnames or []
        rows = list(reader)

    selected: List[Row] = []
    excluded: List[Row] = []
    candidates: List[Row] = []
    include_journal_unknown_pages = not args.strict_pages

    for row in rows:
        for rule in rules:
            match = match_rule(row, rule)
            if not match:
                continue
            match_field, match_value = match
            is_long, reason, pages = is_long_paper(row, rule, args.min_pages, include_journal_unknown_pages)
            annotated = annotate_row(row, rule, match_field, match_value, is_long, reason, pages)
            candidates.append(annotated)
            if is_long:
                selected.append(annotated)
            else:
                excluded.append(annotated)
            break

    if not args.no_dedupe:
        selected = unique_rows(selected)
        excluded = unique_rows(excluded)

    output_columns = preferred_columns(input_columns)
    write_csv(Path(args.output), selected, output_columns)
    write_csv(Path(args.excluded_output), excluded, output_columns)

    cov_rows = coverage_rows(rules, candidates, selected)
    write_csv(
        Path(args.coverage_output),
        cov_rows,
        ["ccf_area", "ccf_rank", "ccf_venue", "ccf_venue_kind", "candidate_matches", "long_paper_matches", "covered", "aliases"],
    )

    area_counts: Dict[str, int] = {}
    venue_counts: Dict[str, int] = {}
    for row in selected:
        area_counts[row["ccf_area"]] = area_counts.get(row["ccf_area"], 0) + 1
        key = f"{row['ccf_area']}/{row['ccf_venue']}"
        venue_counts[key] = venue_counts.get(key, 0) + 1

    print(f"input rows: {len(rows)}", file=sys.stderr)
    print(f"ccf-a candidate matches: {len(candidates)}", file=sys.stderr)
    print(f"selected long papers: {len(selected)}", file=sys.stderr)
    print(f"excluded matched candidates: {len(excluded)}", file=sys.stderr)
    print("selected by area: " + ", ".join(f"{key}={value}" for key, value in sorted(area_counts.items())), file=sys.stderr)
    print("selected by venue: " + ", ".join(f"{key}={value}" for key, value in sorted(venue_counts.items())), file=sys.stderr)
    print(args.output)
    print(args.coverage_output)
    print(args.excluded_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
