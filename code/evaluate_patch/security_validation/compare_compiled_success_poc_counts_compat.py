#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List


SUPPORTED_MODES = {"poc_cmd", "poc_file", "poc_string", "poc_string2", "poc_exit"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare poc match_count between two summary.json files, while being "
            "compatible with both single-patch and multi-patch summary formats."
        )
    )
    parser.add_argument(
        "vul_repos",
        nargs="?",
        default="origin_vuls_output_20260508_origin_true_true",
        help="Baseline output directory or summary.json path",
    )
    parser.add_argument(
        "patch_repos",
        nargs="?",
        default="origin_vuls_output_multi_patch_reinfix_gpt54_true",
        help="Current output directory or summary.json path",
    )
    parser.add_argument("--left-label", default=None, help="Display label for baseline summary")
    parser.add_argument("--right-label", default=None, help="Display label for current summary")
    parser.add_argument(
        "--show-equal",
        action="store_true",
        help="Also show rows where match_count is equal",
    )
    parser.add_argument(
        "--show-skipped",
        action="store_true",
        help="Also print skipped targets or reasons",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_summary_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_dir():
        return path / "summary.json"
    return path


def infer_label(path_str: str) -> str:
    path = Path(path_str)
    if path.name == "summary.json":
        return path.parent.name or str(path.parent)
    return path.name or str(path)


def normalize_item(status: str, item: dict) -> dict | None:
    if not isinstance(item, dict):
        return None

    target_id = item.get("target_id")
    mode = item.get("mode")
    if not target_id or mode not in SUPPORTED_MODES:
        return None

    metrics = item.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}

    return {
        "target_id": target_id,
        "status": status,
        "mode": mode,
        "compile_ok": bool(metrics.get("compile_ok", False)),
        "match_count": int(metrics.get("match_count", 0) or 0),
        "info": item.get("info"),
        "best_patch_label": item.get("best_patch_label"),
        "best_patch_path": item.get("best_patch_path"),
        "successful_patch_count": item.get("successful_patch_count"),
    }


def index_summary(summary: dict) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    for status, items in summary.get("details", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            normalized = normalize_item(status, item)
            if normalized is None:
                continue
            result[normalized["target_id"]] = normalized
    return result


def build_table(headers: List[str], rows: Iterable[Iterable[object]]) -> str:
    string_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in string_rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def render_row(row: List[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)) + " |"

    sep = "|-" + "-|-".join("-" * width for width in widths) + "-|"
    lines = [render_row(headers), sep]
    lines.extend(render_row(row) for row in string_rows)
    return "\n".join(lines)


def print_section(title: str, headers: List[str], rows: List[List[object]]) -> None:
    print(f"\n{title}")
    if not rows:
        print("(none)")
        return
    print(build_table(headers, rows))


def main() -> None:
    args = parse_args()
    left_path = resolve_summary_path(args.vul_repos)
    right_path = resolve_summary_path(args.patch_repos)
    left_label = args.left_label or infer_label(args.vul_repos)
    right_label = args.right_label or infer_label(args.patch_repos)

    left_summary = load_json(left_path)
    right_summary = load_json(right_path)
    left_index = index_summary(left_summary)
    right_index = index_summary(right_summary)

    compared_rows = []
    skipped_rows = []

    for target_id, right_item in sorted(right_index.items()):
        if not right_item["compile_ok"]:
            skipped_rows.append([target_id, "right_compile_not_ok", right_item["status"]])
            continue

        left_item = left_index.get(target_id)
        if left_item is None:
            skipped_rows.append([target_id, "missing_in_left", right_item["status"]])
            continue

        if left_item["mode"] != right_item["mode"]:
            skipped_rows.append(
                [
                    target_id,
                    f"mode_mismatch:{left_item['mode']}!={right_item['mode']}",
                    right_item["status"],
                ]
            )
            continue

        left_count = left_item["match_count"]
        right_count = right_item["match_count"]
        diff = right_count - left_count
        relation = "<" if right_count < left_count else ">" if right_count > left_count else "="
        compared_rows.append(
            {
                "target_id": target_id,
                "mode": right_item["mode"],
                "left_count": left_count,
                "right_count": right_count,
                "diff": diff,
                "relation": relation,
                "left_compile_ok": left_item["compile_ok"],
                "left_status": left_item["status"],
                "right_status": right_item["status"],
                "best_patch_label": right_item.get("best_patch_label"),
                "best_patch_path": right_item.get("best_patch_path"),
                "successful_patch_count": right_item.get("successful_patch_count"),
            }
        )

    less_rows = [row for row in compared_rows if row["relation"] == "<"]
    greater_rows = [row for row in compared_rows if row["relation"] == ">"]
    equal_rows = [row for row in compared_rows if row["relation"] == "="]
    no_vulnerability_rows = [
        row
        for row in compared_rows
        if row["left_compile_ok"]
        and row["left_status"] == "VULNERABLE"
        and row["left_count"] > 0
        and row["right_status"] == "NOT_VULNERABLE"
        and row["right_count"] == 0
    ]

    mode_counter = defaultdict(Counter)
    status_counter = defaultdict(Counter)
    for row in compared_rows:
        mode_counter[row["mode"]][row["relation"]] += 1
        status_counter[row["right_status"]][row["relation"]] += 1

    summary_rows = [
        ["baseline", left_label],
        ["current", right_label],
        ["baseline_indexed_targets", len(left_index)],
        ["current_indexed_targets", len(right_index)],
        ["current_compile_success", len(compared_rows)],
        ["current_lt_baseline", len(less_rows)],
        ["current_no_vulnerability", len(no_vulnerability_rows)],
        ["current_gt_baseline", len(greater_rows)],
        ["current_eq_baseline", len(equal_rows)],
        ["skipped_targets", len(skipped_rows)],
    ]
    print(build_table(["metric", "value"], summary_rows))

    mode_rows = []
    for mode in sorted(SUPPORTED_MODES):
        counts = mode_counter[mode]
        mode_rows.append(
            [
                mode,
                counts["<"] + counts[">"] + counts["="],
                counts["<"],
                counts["="],
                counts[">"],
            ]
        )
    print_section(
        "Breakdown By Mode",
        ["mode", "compile_success_in_current", "current_lt_baseline", "current_eq_baseline", "current_gt_baseline"],
        mode_rows,
    )

    status_rows = []
    for status in sorted(status_counter):
        counts = status_counter[status]
        status_rows.append(
            [
                status,
                counts["<"] + counts[">"] + counts["="],
                counts["<"],
                counts["="],
                counts[">"],
            ]
        )
    print_section(
        f"Breakdown By {right_label} Status",
        ["status", "compile_success_in_current", "current_lt_baseline", "current_eq_baseline", "current_gt_baseline"],
        status_rows,
    )

    less_detail_rows = [
        [
            row["target_id"],
            row["mode"],
            row["left_count"],
            row["right_count"],
            row["diff"],
            row["right_status"],
            row["best_patch_label"] or "",
        ]
        for row in sorted(less_rows, key=lambda x: (x["diff"], x["mode"], x["target_id"]))
    ]
    print_section(
        f"{right_label} < {left_label}",
        ["target_id", "mode", left_label, right_label, "diff", f"{right_label}_status", "best_patch_label"],
        less_detail_rows,
    )

    greater_detail_rows = [
        [
            row["target_id"],
            row["mode"],
            row["left_count"],
            row["right_count"],
            row["diff"],
            row["right_status"],
            row["best_patch_label"] or "",
        ]
        for row in sorted(greater_rows, key=lambda x: (-x["diff"], x["mode"], x["target_id"]))
    ]
    print_section(
        f"{right_label} > {left_label}",
        ["target_id", "mode", left_label, right_label, "diff", f"{right_label}_status", "best_patch_label"],
        greater_detail_rows,
    )

    if args.show_equal:
        equal_detail_rows = [
            [
                row["target_id"],
                row["mode"],
                row["left_count"],
                row["right_count"],
                row["diff"],
                row["right_status"],
                row["best_patch_label"] or "",
            ]
            for row in sorted(equal_rows, key=lambda x: (x["mode"], x["target_id"]))
        ]
        print_section(
            f"{right_label} = {left_label}",
            ["target_id", "mode", left_label, right_label, "diff", f"{right_label}_status", "best_patch_label"],
            equal_detail_rows,
        )

    if args.show_skipped:
        print_section(
            "Skipped",
            ["target_id", "reason", "right_status"],
            skipped_rows,
        )


if __name__ == "__main__":
    main()
