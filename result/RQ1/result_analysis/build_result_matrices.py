#!/usr/bin/env python3
"""从各组补丁验证结果生成 target_id × 工具 的状态矩阵 CSV。

CVE 描述实验中初步判定为 success、但 RQ1 真实 PoC 验证为修复失败的
单元格，以真实 PoC 的“修复失败”为准。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENTS = (
    "CVE 描述验证结果",
    "带漏洞链验证结果",
    "带上游补丁验证结果",
    "带自生成上游补丁验证结果",
    "带自生成上游补丁加漏洞链验证结果",
    "带PoC验证结果",
)
RQ1_MATRIX = "RQ1真实PoC验证结果_矩阵.csv"

SUCCESS = "success"
EMPTY = "empty"
COMPILE_ERROR = "编译错误"
REPAIR_FAILED = "修复失败"
VALID_RESULTS = {SUCCESS, EMPTY, COMPILE_ERROR, REPAIR_FAILED}

TOOL_DIR_RE = re.compile(
    r"^normalized_patches_(?P<tool>.+?)_\d{8}_\d{6}$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="为各组实验生成 target_id × 工具 的修复结果矩阵"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="包含各实验结果文件夹的根目录（默认：脚本所在目录）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="CSV 输出目录（默认：root）",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_latest_pipeline(experiment_dir: Path) -> Path:
    """选择目录名时间戳最大的完整验证批次。"""
    candidates = sorted(
        experiment_dir.glob("nine_patch_validation_*/pipeline_summary.json"),
        key=lambda path: path.parent.name,
    )
    if not candidates:
        raise FileNotFoundError(
            f"{experiment_dir} 下没有 nine_patch_validation_*/pipeline_summary.json"
        )

    # 有些实验重跑过；只有包含全部 patched summary 的批次才可用。
    complete = []
    for pipeline_path in candidates:
        pipeline = load_json(pipeline_path)
        patch_runs = pipeline.get("patch_runs", [])
        if patch_runs and all(
            patched_summary_path(pipeline_path, run).is_file() for run in patch_runs
        ):
            complete.append(pipeline_path)
    if not complete:
        raise RuntimeError(f"{experiment_dir} 下没有完整的验证批次")
    return complete[-1]


def patched_summary_path(pipeline_path: Path, patch_run: dict[str, Any]) -> Path:
    run_dir = (
        f"{int(patch_run['run_number']):02d}_{patch_run['patch_directory']}"
    )
    return pipeline_path.parent / run_dir / "patched" / "summary.json"


def baseline_summary_path(pipeline_path: Path, patch_run: dict[str, Any]) -> Path:
    """用 pipeline 中的 baseline 目录名定位，避免结果目录移动后绝对路径失效。"""
    configured = Path(patch_run["baseline_summary"])
    return pipeline_path.parent / configured.parent.name / "summary.json"


def extract_tool(patch_directory: str) -> str:
    match = TOOL_DIR_RE.match(patch_directory)
    if not match:
        raise ValueError(f"无法从补丁目录名提取工具名：{patch_directory}")
    return match.group("tool")


def index_summary(summary: dict[str, Any], source: Path) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    details = summary.get("details")
    if not isinstance(details, dict):
        raise ValueError(f"summary 缺少 details 对象：{source}")

    for status, items in details.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("target_id"):
                continue
            target_id = str(item["target_id"])
            if target_id in indexed:
                raise ValueError(f"summary 中 target_id 重复：{target_id}（{source}）")
            indexed[target_id] = {**item, "_status": status}
    return indexed


def match_count(item: dict[str, Any]) -> int | None:
    metrics = item.get("metrics")
    if not isinstance(metrics, dict):
        return None
    value = metrics.get("match_count")
    if value is None:
        return None
    return int(value)


def classify(
    baseline_item: dict[str, Any], patched_item: dict[str, Any]
) -> str:
    """按补丁缺失、编译、漏洞次数下降的优先级归类。"""
    patch_candidates = int(patched_item.get("patch_candidates", 0) or 0)
    if patch_candidates == 0:
        return EMPTY

    patched_status = str(patched_item.get("_status", ""))
    metrics = patched_item.get("metrics")
    compile_ok = isinstance(metrics, dict) and bool(metrics.get("compile_ok"))
    if patched_status == "COMPILE_FAILED" or not compile_ok:
        return COMPILE_ERROR

    baseline_count = match_count(baseline_item)
    patched_count = match_count(patched_item)
    if (
        baseline_count is not None
        and patched_count is not None
        and patched_count < baseline_count
    ):
        return SUCCESS

    return REPAIR_FAILED


def build_matrix(
    pipeline_path: Path,
) -> tuple[list[str], list[str], dict[str, dict[str, str]]]:
    pipeline = load_json(pipeline_path)
    patch_runs = sorted(
        pipeline.get("patch_runs", []), key=lambda run: int(run["run_number"])
    )
    if not patch_runs:
        raise ValueError(f"pipeline_summary 没有 patch_runs：{pipeline_path}")

    tools: list[str] = []
    matrix: dict[str, dict[str, str]] = {}
    expected_targets: set[str] | None = None

    for patch_run in patch_runs:
        tool = extract_tool(str(patch_run["patch_directory"]))
        if tool in tools:
            raise ValueError(f"工具名重复：{tool}（{pipeline_path}）")
        tools.append(tool)

        baseline_path = baseline_summary_path(pipeline_path, patch_run)
        patched_path = patched_summary_path(pipeline_path, patch_run)
        baseline = index_summary(load_json(baseline_path), baseline_path)
        patched = index_summary(load_json(patched_path), patched_path)

        targets = set(baseline)
        if expected_targets is None:
            expected_targets = targets
        elif targets != expected_targets:
            raise ValueError(
                f"不同 baseline 的 target_id 集合不一致：{baseline_path}"
            )

        missing_results = targets - set(patched)
        extra_results = set(patched) - targets
        if missing_results or extra_results:
            raise ValueError(
                f"baseline/patched target_id 不一致：{patched_path}；"
                f"缺少={sorted(missing_results)}，多出={sorted(extra_results)}"
            )

        for target_id in targets:
            result = classify(baseline[target_id], patched[target_id])
            matrix.setdefault(target_id, {})[tool] = result

    target_ids = sorted(expected_targets or set())
    return tools, target_ids, matrix


def write_matrix(
    output_path: Path,
    tools: list[str],
    target_ids: list[str],
    matrix: dict[str, dict[str, str]],
) -> Counter[str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    # utf-8-sig 让 Excel 直接打开时能正确识别中文。
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["target_id", *tools])
        for target_id in target_ids:
            row = [matrix[target_id][tool] for tool in tools]
            unknown = set(row) - VALID_RESULTS
            if unknown:
                raise AssertionError(f"出现未知状态：{sorted(unknown)}")
            counts.update(row)
            writer.writerow([target_id, *row])
    return counts


def apply_rq1_failures(
    matrix: dict[str, dict[str, str]],
    tools: list[str],
    rq1_path: Path,
) -> list[tuple[str, str]]:
    """用 RQ1 真实 PoC 的修复失败推翻 CVE 描述实验的 success。"""
    with rq1_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        expected_header = ["target_id", *tools]
        if reader.fieldnames != expected_header:
            raise ValueError(
                "RQ1 矩阵的列名或工具顺序不一致：\n"
                f"期望: {expected_header}\n实际: {reader.fieldnames}"
            )
        rq1_rows = list(reader)

    changes: list[tuple[str, str]] = []
    seen_targets: set[str] = set()
    for row in rq1_rows:
        target_id = row["target_id"]
        if target_id in seen_targets:
            raise ValueError(f"RQ1 矩阵中 target_id 重复：{target_id}")
        seen_targets.add(target_id)
        if target_id not in matrix:
            raise ValueError(f"RQ1 的 target_id 不在 CVE 矩阵中：{target_id}")

        for tool in tools:
            if row[tool] == REPAIR_FAILED and matrix[target_id][tool] == SUCCESS:
                matrix[target_id][tool] = REPAIR_FAILED
                changes.append((target_id, tool))
    return changes


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_dir = (args.output_dir or root).resolve()

    for experiment in EXPERIMENTS:
        experiment_dir = root / experiment
        pipeline_path = find_latest_pipeline(experiment_dir)
        tools, target_ids, matrix = build_matrix(pipeline_path)
        rq1_changes: list[tuple[str, str]] = []
        if experiment == "CVE 描述验证结果":
            rq1_changes = apply_rq1_failures(matrix, tools, root / RQ1_MATRIX)
        output_path = output_dir / f"{experiment}_矩阵.csv"
        counts = write_matrix(output_path, tools, target_ids, matrix)
        count_text = ", ".join(f"{key}={counts[key]}" for key in sorted(VALID_RESULTS))
        rq1_text = f"，RQ1 修正={len(rq1_changes)}" if rq1_changes else ""
        print(
            f"已生成 {output_path}（批次={pipeline_path.parent.name}，"
            f"{len(target_ids)} targets × {len(tools)} tools；{count_text}"
            f"{rq1_text}）"
        )


if __name__ == "__main__":
    main()
