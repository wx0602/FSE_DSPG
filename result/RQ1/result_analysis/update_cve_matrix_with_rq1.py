#!/usr/bin/env python3
"""用 RQ1 真实 PoC 的修复失败修正 CVE 矩阵中的 success。"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from collections import Counter
from pathlib import Path


SUCCESS = "success"
REPAIR_FAILED = "修复失败"
VALID_RESULTS = {SUCCESS, "empty", "编译错误", REPAIR_FAILED}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "当 CVE 矩阵为 success、RQ1 真实 PoC 矩阵为修复失败时，"
            "将 CVE 状态改为修复失败"
        )
    )
    parser.add_argument(
        "--cve",
        type=Path,
        default=root / "CVE 描述验证结果_矩阵.csv",
        help="需要修正的 CVE 矩阵",
    )
    parser.add_argument(
        "--rq1",
        type=Path,
        default=root / "RQ1真实PoC验证结果_矩阵.csv",
        help="RQ1 真实 PoC 矩阵",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要修改的单元格，不写文件",
    )
    return parser.parse_args()


def read_matrix(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"第一列必须是 target_id：{path}")
        rows = list(reader)

    target_ids = [row["target_id"] for row in rows]
    if len(target_ids) != len(set(target_ids)):
        raise ValueError(f"存在重复 target_id：{path}")

    tools = reader.fieldnames[1:]
    for row in rows:
        unknown = {row[tool] for tool in tools} - VALID_RESULTS
        if unknown:
            raise ValueError(
                f"{path} 的 {row['target_id']} 中存在未知状态：{sorted(unknown)}"
            )
    return list(reader.fieldnames), rows


def write_matrix_atomic(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main() -> None:
    args = parse_args()
    cve_path = args.cve.resolve()
    rq1_path = args.rq1.resolve()
    cve_header, cve_rows = read_matrix(cve_path)
    rq1_header, rq1_rows = read_matrix(rq1_path)

    if rq1_header != cve_header:
        raise ValueError(
            "两个矩阵的列名或工具顺序不一致：\n"
            f"CVE: {cve_header}\nRQ1: {rq1_header}"
        )

    tools = cve_header[1:]
    cve_by_target = {row["target_id"]: row for row in cve_rows}
    missing_targets = sorted(
        row["target_id"] for row in rq1_rows if row["target_id"] not in cve_by_target
    )
    if missing_targets:
        raise ValueError(f"RQ1 中的 target_id 不在 CVE 矩阵中：{missing_targets}")

    changes: list[tuple[str, str, str]] = []
    for rq1_row in rq1_rows:
        target_id = rq1_row["target_id"]
        cve_row = cve_by_target[target_id]
        for tool in tools:
            # 仅用真实 PoC 的“修复失败”推翻原来的 success；RQ1 中的
            # empty 代表没有可验证补丁，不应覆盖 CVE 矩阵的状态。
            if cve_row[tool] == SUCCESS and rq1_row[tool] == REPAIR_FAILED:
                cve_row[tool] = REPAIR_FAILED
                changes.append((target_id, tool, REPAIR_FAILED))

    action = "将修改" if args.dry_run else "已修改"
    if not args.dry_run and changes:
        write_matrix_atomic(cve_path, cve_header, cve_rows)

    print(f"{action} {len(changes)} 个单元格：{cve_path}")
    by_reason = Counter(reason for _, _, reason in changes)
    by_tool = Counter(tool for _, tool, _ in changes)
    if changes:
        print("按原因：" + ", ".join(f"{key}={value}" for key, value in by_reason.items()))
        print("按工具：" + ", ".join(f"{key}={by_tool[key]}" for key in tools if by_tool[key]))
        for target_id, tool, reason in changes:
            print(f"  {target_id},{tool}: success -> {reason}")


if __name__ == "__main__":
    main()
