#!/usr/bin/env python3
"""Filter available Java-related tools from local YAML files."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


DEFAULT_OUTPUT = "java_available_tools.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read YAML files with a top-level 'papers' list, count Java-related entries, "
            "and write Java-related entries that have links to a YAML file."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="Input YAML files. Defaults to *.yaml and *.yml in the current directory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"Output YAML path. Default: {DEFAULT_OUTPUT}",
    )
    return parser.parse_args()


def is_java_related(category: Any) -> bool:
    text = str(category or "").strip()
    lowered = text.lower()
    if "java" not in lowered:
        return False
    excluding_markers = ("不含 java", "不含java", "excluding java", "without java")
    return not any(marker in lowered for marker in excluding_markers)


def has_usable_link(entry: dict[str, Any]) -> bool:
    link = str(entry.get("link") or "").strip()
    if not link:
        return False
    unavailable_values = {"n/a", "na", "none", "null", "-"}
    return link.lower() not in unavailable_values


def discover_inputs(output: Path) -> list[Path]:
    candidates = sorted(Path.cwd().glob("*.yaml")) + sorted(Path.cwd().glob("*.yml"))
    output_path = output.resolve()
    return [path for path in candidates if path.resolve() != output_path]


def load_papers(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    papers = data.get("papers", [])
    if not isinstance(papers, list):
        return []
    return [paper for paper in papers if isinstance(paper, dict)]


def normalize_tool(entry: dict[str, Any], source_file: Path, source_index: int) -> dict[str, Any]:
    tool: dict[str, Any] = {
        "source_file": source_file.name,
        "source_index": source_index,
        "category": entry.get("category", ""),
        "title": entry.get("title", ""),
        "link": entry.get("link", ""),
    }
    if "id" in entry:
        tool["id"] = entry["id"]
    return tool


def build_output(input_paths: list[Path]) -> dict[str, Any]:
    source_summaries: list[dict[str, Any]] = []
    tools: list[dict[str, Any]] = []
    available_category_counts: Counter[str] = Counter()
    total_entries = 0
    total_java_related_entries = 0

    for path in input_paths:
        papers = load_papers(path)
        java_related = []
        java_related_available = []

        for source_index, entry in enumerate(papers, start=1):
            if not is_java_related(entry.get("category")):
                continue
            java_related.append(entry)
            if has_usable_link(entry):
                java_related_available.append(entry)
                available_category_counts[str(entry.get("category", ""))] += 1
                tools.append(normalize_tool(entry, path, source_index))

        total_entries += len(papers)
        total_java_related_entries += len(java_related)
        source_summaries.append(
            {
                "source_file": path.name,
                "total_entries": len(papers),
                "java_related_entries": len(java_related),
                "available_java_tools": len(java_related_available),
            }
        )

    return {
        "input_files": [path.name for path in input_paths],
        "source_summaries": source_summaries,
        "total_entries": total_entries,
        "java_related_entries": total_java_related_entries,
        "available_java_tool_count": len(tools),
        "available_java_tool_category_counts": dict(available_category_counts),
        "tools": tools,
    }


def main() -> None:
    args = parse_args()
    input_paths = args.inputs or discover_inputs(args.output)
    input_paths = [path for path in input_paths if path.exists()]
    result = build_output(input_paths)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        yaml.safe_dump(result, file, allow_unicode=True, sort_keys=False, width=100)

    print(f"Scanned {len(input_paths)} YAML files.")
    print(f"Java-related entries: {result['java_related_entries']}")
    print(f"Available Java tools: {result['available_java_tool_count']}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
