#!/usr/bin/env python3
"""导出前五组实验的 PoC 合并成功补丁名单。"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MERGED_ROOT = ROOT / "poc合并"
OUTPUT_ROOT = ROOT / "前五组成功补丁名单"

EXPERIMENTS = (
    ("CVE 描述验证结果_矩阵.csv", "1_仅CVE描述"),
    ("带上游补丁验证结果_矩阵.csv", "2_增加上游补丁"),
    ("带漏洞链验证结果_矩阵.csv", "3_增加漏洞链"),
    ("带自生成上游补丁验证结果_矩阵.csv", "4_增加自生成上游补丁"),
    (
        "带自生成上游补丁加漏洞链验证结果_矩阵.csv",
        "5_自生成上游补丁加漏洞链",
    ),
)

CRITERIA = (
    ("所有PoC都通过", "所有PoC都通过_AND_成功补丁名单.txt"),
    (
        "至少一个PoC通过（部分修复成功）",
        "至少一个PoC通过_OR_成功补丁名单.txt",
    ),
)


def read_success_patches(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"CSV 第一列必须是 target_id：{path}")
        tools = list(reader.fieldnames[1:])
        rows = list(reader)

    if len(rows) != 63 or len(tools) != 9:
        raise ValueError(f"矩阵不是 63×9：{path}")

    patches = [
        f"{tool}__{row['target_id']}.patch"
        for tool in tools
        for row in rows
        if row[tool] == "success"
    ]
    return sorted(patches)


def main() -> None:
    for matrix_name, experiment_folder in EXPERIMENTS:
        output_dir = OUTPUT_ROOT / experiment_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        for criterion_folder, output_name in CRITERIA:
            source = MERGED_ROOT / criterion_folder / matrix_name
            patches = read_success_patches(source)
            output = output_dir / output_name
            output.write_text("\n".join(patches) + "\n", encoding="utf-8")
            print(f"{experiment_folder}/{output_name}: {len(patches)}")


if __name__ == "__main__":
    main()
