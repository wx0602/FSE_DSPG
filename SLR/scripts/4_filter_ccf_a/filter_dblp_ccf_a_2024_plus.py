#!/usr/bin/env python3
"""Filter CCF-A venue papers from DBLP 2024+ metadata."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from filter_all_ccf_a_long_papers import (
    CCF_A_RULES,
    NON_LONG_TERMS,
    VenueRule,
    area_group,
    clean_text,
    match_rule,
    normalize,
    parse_pages,
    preferred_columns,
    unique_rows,
    write_csv,
)


Row = Dict[str, str]

DBLP_ALIAS_EXTENSIONS = {
    "TDSC": ("IEEE Trans. Dependable Secur. Comput.",),
    "TIFS": ("IEEE Trans. Inf. Forensics Secur.",),
    "TNNLS": ("IEEE Trans. Neural Networks Learn. Syst.",),
    "TMC": ("IEEE Trans. Mob. Comput.",),
}

NON_MAIN_TRACK_TERMS = tuple(
    sorted(
        set(NON_LONG_TERMS)
        | {
            "artifact",
            "artifacts",
            "challenge",
            "competition",
            "doctoral consortium",
            "nier",
            "new ideas and emerging results",
            "research track abstracts",
            "shadow pc",
            "tool demo",
            "tool demonstrations",
        }
    )
)


def augmented_rules() -> Tuple[VenueRule, ...]:
    rules: list[VenueRule] = []
    for rule in CCF_A_RULES:
        extra_aliases = DBLP_ALIAS_EXTENSIONS.get(rule.short, ())
        if extra_aliases:
            rule = replace(rule, aliases=tuple(dict.fromkeys(rule.aliases + extra_aliases)))
        rules.append(rule)
    return tuple(rules)


def areas_from_arg(value: str, rules: Sequence[VenueRule]) -> List[str]:
    areas = [item.strip().lower() for item in value.split(",") if item.strip()]
    allowed = {rule.area for rule in rules}
    if not areas or areas == ["all"] or areas == ["*"]:
        return sorted(allowed)
    invalid = sorted(set(areas).difference(allowed))
    if invalid:
        raise SystemExit(f"unknown areas: {', '.join(invalid)}; allowed: {', '.join(sorted(allowed))}")
    return areas


def row_text(row: Row) -> str:
    fields = (
        "series",
        "booktitle",
        "journal",
        "dblp_venue",
        "venue",
        "venue_detail",
        "title",
        "note",
    )
    return " ".join(row.get(field, "") for field in fields)


def non_main_track_reason(row: Row) -> str:
    raw_venue = clean_text(" ".join(row.get(field, "") for field in ("series", "booktitle", "dblp_venue")))
    if "@" in raw_venue:
        return f"co-located/workshop venue: {raw_venue}"

    text = normalize(row_text(row))
    for term in NON_MAIN_TRACK_TERMS:
        if normalize(term) in text:
            return f"non-main-track term: {term}"
    return ""


def annotate_row(row: Row, rule: VenueRule, match_field: str, match_value: str, selected: bool, reason: str) -> Row:
    pages, page_source = parse_pages(row)
    annotated = dict(row)
    annotated["ccf_rank"] = "A"
    annotated["ccf_area"] = rule.area
    annotated["ccf_area_group"] = area_group(rule.area)
    annotated["ccf_venue"] = rule.short
    annotated["ccf_venue_kind"] = rule.kind
    annotated["ccf_match_field"] = match_field
    annotated["ccf_match_value"] = match_value
    annotated["paper_pages"] = "" if pages is None else str(pages)
    annotated["paper_pages_source"] = page_source
    annotated["is_ccf_a_main_track"] = "yes" if selected else "no"
    annotated["ccf_filter_reason"] = reason
    return annotated


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
                "selected_matches": str(selected_count),
                "covered": "yes" if selected_count else "no",
                "aliases": "; ".join(rule.aliases),
                "negative_aliases": "; ".join(rule.negative_aliases),
            }
        )
    return rows


def grouped_output_paths(output: str, prefix: str) -> Dict[str, Path]:
    base = Path(prefix) if prefix else Path(output).with_suffix("")
    return {group: base.with_name(f"{base.name}_{group}.csv") for group in ("se", "ai", "security", "other")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter CCF-A papers from dblp_all_paper_dedup_2024_plus.csv.")
    parser.add_argument("input", nargs="?", default="dblp_all_paper_dedup_2024_plus.csv", help="Input DBLP 2024+ CSV.")
    parser.add_argument("-o", "--output", default="dblp_ccf_a_2024_plus.csv", help="Selected CCF-A output CSV.")
    parser.add_argument("--coverage-output", default="dblp_ccf_a_2024_plus_coverage.csv", help="Coverage summary CSV.")
    parser.add_argument("--excluded-output", default="dblp_ccf_a_2024_plus_excluded_candidates.csv", help="Matched but excluded CSV.")
    parser.add_argument("--group-output-prefix", default="", help="Prefix for selected split CSVs.")
    parser.add_argument(
        "--areas",
        default="all",
        help="Comma-separated areas, or all. Available: ai,se,security,crypto,arch,network,database,graphics_hci,theory.",
    )
    parser.add_argument("--no-dedupe", action="store_true", help="Do not deduplicate matched rows by title.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    all_rules = augmented_rules()
    areas = set(areas_from_arg(args.areas, all_rules))
    rules = [rule for rule in all_rules if rule.area in areas]

    input_path = Path(args.input)
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        input_columns = reader.fieldnames or []
        rows = list(reader)

    selected: list[Row] = []
    excluded: list[Row] = []
    candidates: list[Row] = []

    for row in rows:
        for rule in rules:
            match = match_rule(row, rule)
            if not match:
                continue
            match_field, match_value = match
            reason = non_main_track_reason(row)
            is_selected = not reason
            annotated = annotate_row(
                row,
                rule,
                match_field,
                match_value,
                selected=is_selected,
                reason="ccf-a main venue match" if is_selected else reason,
            )
            candidates.append(annotated)
            if is_selected:
                selected.append(annotated)
            else:
                excluded.append(annotated)
            break

    if not args.no_dedupe:
        selected = unique_rows(selected)
        excluded = unique_rows(excluded)

    metadata = [
        "ccf_rank",
        "ccf_area_group",
        "ccf_area",
        "ccf_venue",
        "ccf_venue_kind",
        "ccf_match_field",
        "ccf_match_value",
        "paper_pages",
        "paper_pages_source",
        "is_ccf_a_main_track",
        "ccf_filter_reason",
    ]
    output_columns = metadata + [column for column in input_columns if column not in metadata]
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
            "selected_matches",
            "covered",
            "aliases",
            "negative_aliases",
        ],
    )

    group_paths = grouped_output_paths(args.output, args.group_output_prefix)
    for group, path in group_paths.items():
        write_csv(path, [row for row in selected if row.get("ccf_area_group") == group], output_columns)

    group_counts: dict[str, int] = {}
    venue_counts: dict[str, int] = {}
    for row in selected:
        group_counts[row["ccf_area_group"]] = group_counts.get(row["ccf_area_group"], 0) + 1
        key = f"{row['ccf_area']}/{row['ccf_venue']}"
        venue_counts[key] = venue_counts.get(key, 0) + 1

    print(f"input rows: {len(rows)}", file=sys.stderr)
    print(f"ccf-a candidate matches: {len(candidates)}", file=sys.stderr)
    print(f"selected ccf-a main-track/journal papers: {len(selected)}", file=sys.stderr)
    print(f"excluded matched candidates: {len(excluded)}", file=sys.stderr)
    print("selected by group: " + ", ".join(f"{key}={group_counts.get(key, 0)}" for key in ("se", "ai", "security", "other")), file=sys.stderr)
    print("selected by venue: " + ", ".join(f"{key}={value}" for key, value in sorted(venue_counts.items())), file=sys.stderr)
    print(args.output)
    print(args.coverage_output)
    print(args.excluded_output)
    for group in ("se", "ai", "security", "other"):
        print(group_paths[group])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
