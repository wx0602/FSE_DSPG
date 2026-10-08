#!/usr/bin/env python3
"""Filter CCF-A long papers from the merged four-source paper CSV.

Default input:
  all_papers_merged_dedup.csv

The rule table covers CCF-A venues that appear in the merged CSV, including AI,
software engineering/programming languages, security, architecture/systems,
networking, databases, graphics/HCI, theory, and cryptography. Conference
papers are selected when page count is at least --min-pages. Journal articles
with missing page counts are kept by default because several exports omit
article length.

Outputs:
  all_ccf_a_long_papers.csv
  all_ccf_a_coverage.csv
  all_ccf_a_excluded_candidates.csv

Usage:
  python3 filter_all_ccf_a_long_papers.py
  python3 filter_all_ccf_a_long_papers.py --min-pages 8
  python3 filter_all_ccf_a_long_papers.py --strict-pages
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
AREA_GROUPS = ("se", "ai", "security", "other")


@dataclass(frozen=True)
class VenueRule:
    area: str
    short: str
    kind: str
    aliases: Tuple[str, ...]
    negative_aliases: Tuple[str, ...] = ()


CCF_A_RULES: Tuple[VenueRule, ...] = (
    # AI / ML / data mining / IR / web / NLP / vision / multimedia.
    VenueRule("ai", "AAAI", "conference", ("AAAI", "AAAI Conference on Artificial Intelligence"), ("AIES",)),
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
    VenueRule(
        "ai",
        "AIJ",
        "journal",
        ("Artificial Intelligence", "Artif. Intell.", "AIJ"),
        (
            "Engineering Applications of Artificial Intelligence",
            "Applied Artificial Intelligence",
            "Artificial Intelligence Review",
            "Artificial Intelligence in Medicine",
            "IEEE Transactions on Artificial Intelligence",
        ),
    ),
    VenueRule(
        "ai",
        "TPAMI",
        "journal",
        ("IEEE Trans. Pattern Anal. Mach. Intell.", "IEEE Transactions on Pattern Analysis and Machine Intelligence", "TPAMI"),
    ),
    VenueRule("ai", "IJCV", "journal", ("Int. J. Comput. Vis.", "International Journal of Computer Vision", "IJCV")),
    VenueRule("ai", "TIP", "journal", ("IEEE Trans. Image Process.", "IEEE Transactions on Image Processing", "TIP")),
    VenueRule(
        "ai",
        "TNNLS",
        "journal",
        ("IEEE Trans. Neural Netw. Learn. Syst.", "IEEE Transactions on Neural Networks and Learning Systems", "TNNLS"),
    ),
    VenueRule("ai", "Computational Linguistics", "journal", ("Computational Linguistics",)),
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
    VenueRule("se", "TOPLAS", "journal", ("ACM Trans. Program. Lang. Syst.", "ACM Transactions on Programming Languages and Systems", "TOPLAS")),
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
    VenueRule("security", "IEEE S&P", "conference", ("IEEE S&P", "IEEE Symposium on Security and Privacy", "IEEE Symposium on Security & Privacy", "SP")),
    VenueRule("security", "USENIX Security", "conference", ("USENIX Security", "USENIX Security Symposium")),
    VenueRule("security", "NDSS", "conference", ("NDSS", "Network and Distributed System Security Symposium")),
    VenueRule("security", "TOPS", "journal", ("ACM Trans. Priv. Secur.", "ACM Transactions on Privacy and Security", "TOPS")),
    VenueRule("security", "TDSC", "journal", ("IEEE Trans. Dependable Secure Comput.", "IEEE Transactions on Dependable and Secure Computing", "TDSC")),
    VenueRule("security", "TIFS", "journal", ("IEEE Trans. Inf. Forensics Security", "IEEE Transactions on Information Forensics and Security", "TIFS")),
    VenueRule("crypto", "CRYPTO", "conference", ("CRYPTO", "International Cryptology Conference")),
    VenueRule("crypto", "EUROCRYPT", "conference", ("EUROCRYPT", "Theory and Applications of Cryptographic Techniques")),
    VenueRule("crypto", "Journal of Cryptology", "journal", ("Journal of Cryptology",)),
    # Architecture / systems / storage / EDA.
    VenueRule("arch", "ISCA", "conference", ("ISCA", "International Symposium on Computer Architecture")),
    VenueRule("arch", "MICRO", "conference", ("MICRO", "International Symposium on Microarchitecture")),
    VenueRule("arch", "HPCA", "conference", ("HPCA", "High-Performance Computer Architecture")),
    VenueRule(
        "arch",
        "ASPLOS",
        "conference",
        ("ASPLOS", "Architectural Support for Programming Languages and Operating Systems"),
    ),
    VenueRule("arch", "PPoPP", "conference", ("PPoPP", "Principles and Practice of Parallel Programming")),
    VenueRule("arch", "FAST", "conference", ("FAST", "File and Storage Technologies")),
    VenueRule("arch", "DAC", "conference", ("DAC", "Design Automation Conference")),
    # Networking.
    VenueRule(
        "network",
        "SIGCOMM",
        "conference",
        ("ACM SIGCOMM", "SIGCOMM Conference", "SIGCOMM"),
        ("Posters and Demos",),
    ),
    VenueRule("network", "MobiCom", "conference", ("MobiCom", "Mobile Computing and Networking")),
    VenueRule("network", "INFOCOM", "conference", ("INFOCOM", "IEEE International Conference on Computer Communications")),
    VenueRule("network", "NSDI", "conference", ("NSDI", "Networked Systems Design and Implementation")),
    VenueRule("network", "TON", "journal", ("IEEE/ACM Trans. Netw.", "IEEE/ACM Transactions on Networking", "TON")),
    VenueRule("network", "JSAC", "journal", ("IEEE J. Sel. Areas Commun.", "IEEE Journal on Selected Areas in Communications", "JSAC")),
    VenueRule("network", "TMC", "journal", ("IEEE Trans. Mobile Comput.", "IEEE Transactions on Mobile Computing", "TMC")),
    # Databases / data management.
    VenueRule(
        "database",
        "SIGMOD",
        "conference",
        ("SIGMOD", "ACM SIGMOD", "International Conference on Management of Data"),
        ("Companion",),
    ),
    VenueRule("database", "VLDB", "conference", ("VLDB", "Very Large Data Bases")),
    VenueRule("database", "ICDE", "conference", ("ICDE", "IEEE International Conference on Data Engineering")),
    VenueRule("database", "PODS", "conference", ("PODS", "Principles of Database Systems")),
    VenueRule("database", "TODS", "journal", ("ACM Trans. Database Syst.", "ACM Transactions on Database Systems", "TODS")),
    VenueRule("database", "TKDE", "journal", ("IEEE Trans. Knowl. Data Eng.", "IEEE Transactions on Knowledge and Data Engineering", "TKDE")),
    VenueRule("database", "PVLDB", "journal", ("Proc. VLDB Endow.", "Proceedings of the VLDB Endowment", "PVLDB")),
    VenueRule("database", "VLDBJ", "journal", ("The VLDB Journal", "VLDB Journal", "VLDBJ")),
    # Graphics / visualization / HCI.
    VenueRule(
        "graphics_hci",
        "SIGGRAPH",
        "conference",
        ("ACM SIGGRAPH", "SIGGRAPH Conference", "SIGGRAPH"),
        ("SIGGRAPH/Eurographics Symposium", "Symposium on Computer Animation", "Posters", "Courses"),
    ),
    VenueRule(
        "graphics_hci",
        "SIGGRAPH Asia",
        "conference",
        ("SIGGRAPH Asia",),
        ("Posters", "Courses", "Technical Communications"),
    ),
    VenueRule(
        "graphics_hci",
        "CHI",
        "conference",
        ("CHI Conference on Human Factors in Computing Systems", "ACM CHI Conference", "CHI"),
        ("Extended Abstracts",),
    ),
    VenueRule("graphics_hci", "UIST", "conference", ("UIST", "User Interface Software and Technology")),
    VenueRule("graphics_hci", "TOG", "journal", ("ACM Trans. Graph.", "ACM Transactions on Graphics", "TOG")),
    VenueRule(
        "graphics_hci",
        "TVCG",
        "journal",
        ("IEEE Trans. Vis. Comput. Graph.", "IEEE Transactions on Visualization and Computer Graphics", "TVCG"),
    ),
    # Theory / formal methods.
    VenueRule("theory", "STOC", "conference", ("STOC", "Symposium on Theory of Computing")),
    VenueRule("theory", "FOCS", "conference", ("FOCS", "Foundations of Computer Science")),
    VenueRule("theory", "SODA", "conference", ("SODA", "Symposium on Discrete Algorithms")),
    VenueRule("theory", "CAV", "conference", ("CAV", "Computer Aided Verification")),
    VenueRule("theory", "LICS", "conference", ("LICS", "Logic in Computer Science")),
    VenueRule("theory", "JACM", "journal", ("J. ACM", "Journal of the ACM", "JACM")),
    VenueRule("theory", "SICOMP", "journal", ("SIAM J. Comput.", "SIAM Journal on Computing", "SICOMP")),
    VenueRule("theory", "TOCL", "journal", ("ACM Trans. Comput. Logic", "ACM Transactions on Computational Logic", "TOCL")),
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
    "tool demonstration",
    "experience report",
    "extended abstracts",
    "abstracts",
    "posters",
    "demos",
    "course",
    "courses",
    "technical communications",
)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def split_merged_values(value: str) -> List[str]:
    return [clean_text(part) for part in re.split(r"\s+\|\|\s+", value or "") if clean_text(part)]


def normalize(value: str) -> str:
    value = clean_text(value).lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return clean_text(value)


def abbreviation_match(alias: str, haystack: str) -> bool:
    alias_norm = normalize(alias)
    hay_norm = normalize(haystack)
    if not alias_norm:
        return False
    if len(alias_norm) <= 12 and " " not in alias_norm:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(alias_norm)}(?![a-z0-9])", hay_norm))
    return alias_norm in hay_norm


def journal_name_match(alias: str, value: str) -> bool:
    alias_norm = normalize(alias)
    if not alias_norm:
        return False
    for part in split_merged_values(value) or [value]:
        part_norm = normalize(part)
        if not part_norm:
            continue
        if len(alias_norm) <= 12 and " " not in alias_norm:
            if alias_norm == part_norm:
                return True
            continue
        if alias_norm == part_norm:
            return True
    return False


def field_has_negative_alias(rule: VenueRule, value: str) -> bool:
    return any(abbreviation_match(alias, value) for alias in rule.negative_aliases)


def conference_match_fields(row: Row) -> Tuple[str, ...]:
    venue_type = normalize(row.get("venue_type", ""))
    fields = ["series", "booktitle"]
    if venue_type != "journal":
        fields.extend(["venue", "venue_detail"])
    if normalize(row.get("entry_type", "")) == "proceedings":
        fields.append("title")
    return tuple(fields)


def journal_match_fields(row: Row) -> Tuple[str, ...]:
    fields = ["journal"]
    if "journal" in normalize(row.get("venue_type", "")):
        fields.append("venue")
    return tuple(fields)


def match_rule(row: Row, rule: VenueRule) -> Optional[Tuple[str, str]]:
    fields = journal_match_fields(row) if rule.kind == "journal" else conference_match_fields(row)
    for field in fields:
        value = clean_text(row.get(field, ""))
        if not value or field_has_negative_alias(rule, value):
            continue

        if rule.kind == "journal":
            if any(journal_name_match(alias, value) for alias in rule.aliases):
                return field, value
        elif any(abbreviation_match(alias, value) for alias in rule.aliases):
            return field, value
    return None


def parse_numpages(value: str) -> List[int]:
    counts = []
    for part in split_merged_values(value):
        match = re.search(r"\d+", part)
        if match:
            counts.append(int(match.group(0)))
    return counts


def parse_page_ranges(value: str) -> List[int]:
    counts = []
    for part in split_merged_values(value):
        match = re.search(r"(\d+)\s*[-–]\s*(\d+)", part)
        if not match:
            continue
        start, end = int(match.group(1)), int(match.group(2))
        if end >= start:
            counts.append(end - start + 1)
    return counts


def parse_pages(row: Row) -> Tuple[Optional[int], str]:
    counts = parse_numpages(row.get("numpages", ""))
    if counts:
        return max(counts), "numpages"

    counts = parse_page_ranges(row.get("pages", ""))
    if counts:
        return max(counts), "pages"

    return None, "missing"


def non_long_reason(row: Row) -> str:
    entry_type = normalize(row.get("entry_type", ""))
    if entry_type in {"proceedings", "book"}:
        return f"entry_type={entry_type}"

    if entry_type and entry_type not in {"article", "inproceedings", "inbook"}:
        return f"unsupported entry_type={entry_type}"

    text = normalize(
        " ".join(
            row.get(field, "")
            for field in ("series", "booktitle", "journal", "venue", "venue_detail", "title", "note")
        )
    )
    for term in NON_LONG_TERMS:
        if normalize(term) in text:
            return f"non-main-track term: {term}"
    return ""


def is_long_paper(
    row: Row,
    rule: VenueRule,
    min_pages: int,
    include_journal_unknown_pages: bool,
    include_conference_missing_pages: bool,
) -> Tuple[bool, str, Optional[int]]:
    reason = non_long_reason(row)
    if reason:
        return False, reason, None

    pages, page_source = parse_pages(row)
    if pages is not None and pages >= min_pages:
        return True, f"{page_source}={pages} >= {min_pages}", pages
    if pages is not None:
        return False, f"{page_source}={pages} < {min_pages}", pages

    entry_type = normalize(row.get("entry_type", ""))
    if rule.kind == "journal" and entry_type == "article" and include_journal_unknown_pages:
        return True, "journal article with missing page count", pages

    if rule.kind == "conference" and entry_type == "inproceedings" and include_conference_missing_pages:
        return True, "conference paper with missing page count; kept by option", pages

    return False, "missing page count", pages


def areas_from_arg(value: str) -> List[str]:
    areas = [item.strip().lower() for item in value.split(",") if item.strip()]
    allowed = {rule.area for rule in CCF_A_RULES}
    if not areas or areas == ["all"] or areas == ["*"]:
        return sorted(allowed)
    invalid = sorted(set(areas).difference(allowed))
    if invalid:
        raise SystemExit(f"unknown areas: {', '.join(invalid)}; allowed: {', '.join(sorted(allowed))}")
    return areas


def area_group(area: str) -> str:
    if area == "se":
        return "se"
    if area == "ai":
        return "ai"
    if area in {"security", "crypto"}:
        return "security"
    return "other"


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
    annotated["ccf_area_group"] = area_group(rule.area)
    annotated["ccf_venue"] = rule.short
    annotated["ccf_venue_kind"] = rule.kind
    annotated["ccf_match_field"] = match_field
    annotated["ccf_match_value"] = match_value
    annotated["paper_pages"] = "" if pages is None else str(pages)
    annotated["is_long_paper"] = "yes" if is_long else "no"
    annotated["long_paper_reason"] = long_reason
    return annotated


def dedupe_key(row: Row) -> str:
    title = normalize(row.get("title", ""))
    if title:
        return "title:" + title
    doi = normalize(row.get("doi", ""))
    if doi:
        return "doi:" + doi
    url = normalize(row.get("url", ""))
    if url:
        return "url:" + url
    return "record:" + normalize(row.get("source_records", ""))


def unique_rows(rows: Iterable[Row]) -> List[Row]:
    seen = set()
    output = []
    for row in rows:
        key = dedupe_key(row)
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def preferred_columns(input_columns: Sequence[str]) -> List[str]:
    metadata = [
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
                "ccf_area_group": area_group(rule.area),
                "ccf_rank": "A",
                "ccf_venue": rule.short,
                "ccf_venue_kind": rule.kind,
                "candidate_matches": str(candidate_count),
                "long_paper_matches": str(selected_count),
                "covered": "yes" if selected_count else "no",
                "aliases": "; ".join(rule.aliases),
                "negative_aliases": "; ".join(rule.negative_aliases),
            }
        )
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter CCF-A long papers from all_papers_merged_dedup.csv.")
    parser.add_argument("input", nargs="?", default="all_papers_merged_dedup.csv", help="Input merged CSV.")
    parser.add_argument("-o", "--output", default="all_ccf_a_long_papers.csv", help="Filtered long-paper CSV output.")
    parser.add_argument("--coverage-output", default="all_ccf_a_coverage.csv", help="Coverage summary CSV output.")
    parser.add_argument("--excluded-output", default="all_ccf_a_excluded_candidates.csv", help="Matched but excluded candidate CSV output.")
    parser.add_argument(
        "--group-output-prefix",
        default="",
        help="Prefix for selected long-paper split CSVs. Default uses the output filename without .csv.",
    )
    parser.add_argument(
        "--areas",
        default="all",
        help="Comma-separated areas, or all. Available: ai,se,security,crypto,arch,network,database,graphics_hci,theory.",
    )
    parser.add_argument("--min-pages", type=int, default=8, help="Minimum page count for conference long papers.")
    parser.add_argument(
        "--strict-pages",
        action="store_true",
        help="Require explicit page count for journal articles too.",
    )
    parser.add_argument(
        "--include-conference-missing-pages",
        action="store_true",
        help="Keep CCF-A conference matches even when page count is missing.",
    )
    parser.add_argument("--no-dedupe", action="store_true", help="Do not deduplicate matched rows by title.")
    return parser


def grouped_output_paths(output: str, prefix: str) -> Dict[str, Path]:
    base = Path(prefix) if prefix else Path(output).with_suffix("")
    return {group: base.with_name(f"{base.name}_{group}.csv") for group in AREA_GROUPS}


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
            is_long, reason, pages = is_long_paper(
                row,
                rule,
                args.min_pages,
                include_journal_unknown_pages,
                args.include_conference_missing_pages,
            )
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
    write_csv(
        Path(args.coverage_output),
        coverage_rows(rules, candidates, selected),
        [
            "ccf_area",
            "ccf_area_group",
            "ccf_rank",
            "ccf_venue",
            "ccf_venue_kind",
            "candidate_matches",
            "long_paper_matches",
            "covered",
            "aliases",
            "negative_aliases",
        ],
    )

    group_paths = grouped_output_paths(args.output, args.group_output_prefix)
    for group, path in group_paths.items():
        write_csv(path, [row for row in selected if row.get("ccf_area_group") == group], output_columns)

    group_counts: Dict[str, int] = {}
    area_counts: Dict[str, int] = {}
    venue_counts: Dict[str, int] = {}
    for row in selected:
        group_counts[row["ccf_area_group"]] = group_counts.get(row["ccf_area_group"], 0) + 1
        area_counts[row["ccf_area"]] = area_counts.get(row["ccf_area"], 0) + 1
        key = f"{row['ccf_area']}/{row['ccf_venue']}"
        venue_counts[key] = venue_counts.get(key, 0) + 1

    print(f"input rows: {len(rows)}", file=sys.stderr)
    print(f"ccf-a candidate matches: {len(candidates)}", file=sys.stderr)
    print(f"selected long papers: {len(selected)}", file=sys.stderr)
    print(f"excluded matched candidates: {len(excluded)}", file=sys.stderr)
    print("selected by group: " + ", ".join(f"{key}={group_counts.get(key, 0)}" for key in AREA_GROUPS), file=sys.stderr)
    print("selected by area: " + ", ".join(f"{key}={value}" for key, value in sorted(area_counts.items())), file=sys.stderr)
    print("selected by venue: " + ", ".join(f"{key}={value}" for key, value in sorted(venue_counts.items())), file=sys.stderr)
    print(args.output)
    print(args.coverage_output)
    print(args.excluded_output)
    for group in AREA_GROUPS:
        print(group_paths[group])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
