#!/usr/bin/env python3
"""统计“自生成上游补丁+漏洞链”相对其他实验独有的修复成功数。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from build_result_matrices import build_matrix, find_latest_pipeline


MERGED_ROOT = ROOT / "poc合并"
COMBINED = "带自生成上游补丁加漏洞链验证结果_矩阵.csv"
SELF_GENERATED = "带自生成上游补丁验证结果_矩阵.csv"
VULNERABILITY_CHAIN = "带漏洞链验证结果_矩阵.csv"

CRITERIA = (
    ("所有PoC都通过", "所有PoC都通过_AND"),
    ("至少一个PoC通过（部分修复成功）", "至少一个PoC通过_OR"),
)

OUTPUTS = (
    (
        ROOT / "组合组有_但自生成上游补丁和漏洞链均无_各工具成功数.csv",
        "self_and_chain_absent",
    ),
    (
        ROOT / "组合组有_但漏洞链和上游仓库均无_各工具成功数.csv",
        "chain_and_repository_absent",
    ),
)


def read_success_sets(path: Path) -> tuple[list[str], dict[str, set[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"CSV 第一列必须是 target_id：{path}")
        tools = list(reader.fieldnames[1:])
        rows = list(reader)

    if len(rows) != 63 or len(tools) != 9:
        raise ValueError(f"矩阵不是 63×9：{path}")
    return tools, {
        tool: {row["target_id"] for row in rows if row[tool] == "success"}
        for tool in tools
    }


def read_upstream_repository_success_sets(
) -> tuple[list[str], dict[str, set[str]]]:
    pipeline = find_latest_pipeline(WORKSPACE_ROOT / "带上游仓库验证结果")
    tools, targets, matrix = build_matrix(pipeline)
    if len(targets) != 63 or len(tools) != 9:
        raise ValueError(f"上游仓库矩阵不是 63×9：{pipeline}")
    return tools, {
        tool: {target for target in targets if matrix[target][tool] == "success"}
        for tool in tools
    }


def calculate() -> tuple[list[str], dict[str, dict[str, dict[str, int]]]]:
    upstream_tools, upstream = read_upstream_repository_success_sets()
    results: dict[str, dict[str, dict[str, int]]] = {
        key: {} for _, key in OUTPUTS
    }

    for criterion_folder, criterion_label in CRITERIA:
        folder = MERGED_ROOT / criterion_folder
        tools, combined = read_success_sets(folder / COMBINED)
        self_tools, self_generated = read_success_sets(folder / SELF_GENERATED)
        chain_tools, chain = read_success_sets(folder / VULNERABILITY_CHAIN)
        if tools != self_tools or tools != chain_tools or tools != upstream_tools:
            raise ValueError(f"工具列或顺序不一致：{criterion_folder}")

        results["self_and_chain_absent"][criterion_label] = {
            tool: len(combined[tool] - self_generated[tool] - chain[tool])
            for tool in tools
        }
        results["chain_and_repository_absent"][criterion_label] = {
            tool: len(combined[tool] - chain[tool] - upstream[tool])
            for tool in tools
        }

    return upstream_tools, results


def main() -> None:
    tools, results = calculate()
    criterion_labels = [label for _, label in CRITERIA]
    for output, result_key in OUTPUTS:
        with output.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["工具名", *criterion_labels])
            for tool in tools:
                writer.writerow(
                    [tool, *(results[result_key][label][tool] for label in criterion_labels)]
                )
        print(f"已生成：{output}")


if __name__ == "__main__":
    main()
