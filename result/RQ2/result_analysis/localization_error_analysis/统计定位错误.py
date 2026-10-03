#!/usr/bin/env python3
"""按补丁修改文件与 baseline 的交集统计定位是否正确。"""

from __future__ import annotations

import argparse
import csv
import re
import shlex
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BASELINE = Path(
    "/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline"
)


@dataclass(frozen=True)
class Result:
    method: str
    patch_name: str
    generated_files: tuple[str, ...]
    baseline_files: tuple[str, ...]
    overlap_files: tuple[str, ...]
    baseline_exists: bool

    @property
    def correct(self) -> bool:
        return bool(self.overlap_files)

    @property
    def reason(self) -> str:
        if not self.baseline_exists:
            return "缺少同名 baseline 补丁"
        if not self.generated_files:
            return "生成补丁未解析到修改文件"
        if not self.baseline_files:
            return "baseline 补丁未解析到修改文件"
        return "生成补丁与 baseline 修改文件无交集"


def normalize_path(raw_path: str) -> str | None:
    path = raw_path.strip()
    if not path or path == "/dev/null":
        return None
    if (path.startswith('"') and path.endswith('"')):
        try:
            parsed = shlex.split(path)
            if parsed:
                path = parsed[0]
        except ValueError:
            pass
    return re.sub(r"^[ab]/", "", path)


def modified_files(patch_path: Path) -> tuple[str, ...]:
    """提取 diff --git、--- 和 +++ 头中的仓库相对路径。"""
    files: set[str] = set()
    text = patch_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        candidates: list[str] = []
        if line.startswith("diff --git "):
            try:
                fields = shlex.split(line)
            except ValueError:
                fields = line.split()
            candidates = fields[2:4]
        elif line.startswith(("--- ", "+++ ")):
            candidates = [line[4:].split("\t", 1)[0]]

        for candidate in candidates:
            normalized = normalize_path(candidate)
            if normalized is not None:
                files.add(normalized)
    return tuple(sorted(files))


def method_name(directory_name: str) -> str:
    match = re.fullmatch(r"normalized_patches_(.+)_\d{8}_\d{6}", directory_name)
    return match.group(1) if match else directory_name


def collect(normalized_root: Path, baseline_root: Path) -> list[Result]:
    results: list[Result] = []
    for method_dir in sorted(path for path in normalized_root.iterdir() if path.is_dir()):
        method = method_name(method_dir.name)
        for generated_patch in sorted(method_dir.glob("*.patch")):
            baseline_patch = baseline_root / generated_patch.name
            baseline_exists = baseline_patch.is_file()
            generated = modified_files(generated_patch)
            baseline = modified_files(baseline_patch) if baseline_exists else ()
            results.append(
                Result(
                    method=method,
                    patch_name=generated_patch.name,
                    generated_files=generated,
                    baseline_files=baseline,
                    overlap_files=tuple(sorted(set(generated) & set(baseline))),
                    baseline_exists=baseline_exists,
                )
            )
    return results


def group_counts(results: list[Result]) -> list[tuple[str, int, int, int]]:
    grouped: dict[str, list[Result]] = {}
    for result in results:
        grouped.setdefault(result.method, []).append(result)
    rows = []
    for method, method_results in grouped.items():
        total = len(method_results)
        correct = sum(result.correct for result in method_results)
        rows.append((method, total, correct, total - correct))
    return rows


def write_summary_csv(output_dir: Path, counts: list[tuple[str, int, int, int]]) -> None:
    output = output_dir / "定位统计汇总.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["方法", "补丁总数", "定位正确数", "定位错误数", "正确率", "错误率"])
        for method, total, correct, wrong in counts:
            writer.writerow(
                [method, total, correct, wrong, f"{correct / total:.2%}", f"{wrong / total:.2%}"]
            )
        total = sum(row[1] for row in counts)
        correct = sum(row[2] for row in counts)
        wrong = sum(row[3] for row in counts)
        writer.writerow(
            ["合计", total, correct, wrong, f"{correct / total:.2%}", f"{wrong / total:.2%}"]
        )


def write_wrong_csv(output_dir: Path, results: list[Result]) -> None:
    output = output_dir / "定位错误明细.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["方法", "补丁文件", "错误原因", "生成补丁修改文件", "baseline 修改文件"])
        for result in results:
            if result.correct:
                continue
            writer.writerow(
                [
                    result.method,
                    result.patch_name,
                    result.reason,
                    " | ".join(result.generated_files),
                    " | ".join(result.baseline_files),
                ]
            )


def wrong_patch_groups(results: list[Result]) -> list[tuple[str, tuple[str, ...]]]:
    grouped: dict[str, list[str]] = {}
    for result in results:
        if not result.correct:
            grouped.setdefault(result.patch_name, []).append(result.method)
    return [(patch_name, tuple(methods)) for patch_name, methods in sorted(grouped.items())]


def write_wrong_patch_summary_csv(output_dir: Path, results: list[Result]) -> None:
    output = output_dir / "定位错误按补丁汇总.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["补丁文件", "定位错误方法数", "定位错误方法"])
        for patch_name, methods in wrong_patch_groups(results):
            writer.writerow([patch_name, len(methods), " | ".join(methods)])


def write_report(
    output_dir: Path,
    normalized_root: Path,
    baseline_root: Path,
    counts: list[tuple[str, int, int, int]],
    results: list[Result],
) -> None:
    total = len(results)
    correct = sum(result.correct for result in results)
    wrong = total - correct
    missing = sum(not result.baseline_exists for result in results)
    unparsed_generated = sum(not result.generated_files for result in results)
    unparsed_baseline = sum(result.baseline_exists and not result.baseline_files for result in results)
    wrong_groups = wrong_patch_groups(results)

    lines = [
        "# 正则化补丁定位统计",
        "",
        "## 统计结论",
        "",
        f"- 正则化补丁总数：{total}",
        f"- 定位正确：{correct}（{correct / total:.2%}）",
        f"- 定位有问题：{wrong} 个方法-补丁实例（{wrong / total:.2%}）",
        f"- 定位有问题的补丁文件：{len(wrong_groups)} 个（跨方法同名补丁去重）",
        "",
        "## 判定口径",
        "",
        "以补丁文件名查找对应的 baseline 补丁，分别提取两份补丁修改的仓库相对文件路径。两者只要存在至少一个完全相同的文件路径，即判定为定位正确；没有交集则判定为定位有问题。`a/`、`b/` 前缀会在比较前去除。",
        "",
        f"- 正则化补丁目录：`{normalized_root}`",
        f"- baseline 目录：`{baseline_root}`",
        f"- 缺少同名 baseline：{missing}",
        f"- 生成补丁未解析到文件路径：{unparsed_generated}",
        f"- baseline 未解析到文件路径：{unparsed_baseline}",
        "",
        "## 分方法汇总",
        "",
        "| 方法 | 补丁总数 | 定位正确 | 定位有问题 | 正确率 | 错误率 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, method_total, method_correct, method_wrong in counts:
        lines.append(
            f"| {method} | {method_total} | {method_correct} | {method_wrong} | "
            f"{method_correct / method_total:.2%} | {method_wrong / method_total:.2%} |"
        )
    lines.extend(
        [
            f"| **合计** | **{total}** | **{correct}** | **{wrong}** | **{correct / total:.2%}** | **{wrong / total:.2%}** |",
            "",
            "## 去重后的错误补丁",
            "",
            "| 补丁文件 | 定位错误方法数 | 定位错误方法 |",
            "|---|---:|---|",
        ]
    )
    for patch_name, methods in wrong_groups:
        lines.append(f"| {patch_name} | {len(methods)} | {', '.join(methods)} |")
    lines.extend(
        [
            "",
            f"完整的 {wrong} 条错误实例及两边修改文件路径见 `定位错误明细.csv`；按补丁去重的结果见 `定位错误按补丁汇总.csv`。",
            "",
        ]
    )
    (output_dir / "定位统计报告.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized-root", type=Path, default=project_root / "正则化的补丁")
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output-dir", type=Path, default=script_dir)
    args = parser.parse_args()

    if not args.normalized_root.is_dir():
        parser.error(f"正则化补丁目录不存在：{args.normalized_root}")
    if not args.baseline_root.is_dir():
        parser.error(f"baseline 目录不存在：{args.baseline_root}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results = collect(args.normalized_root, args.baseline_root)
    if not results:
        parser.error(f"未找到正则化补丁：{args.normalized_root}")
    counts = group_counts(results)
    write_summary_csv(args.output_dir, counts)
    write_wrong_csv(args.output_dir, results)
    write_wrong_patch_summary_csv(args.output_dir, results)
    write_report(
        args.output_dir,
        args.normalized_root.resolve(),
        args.baseline_root.resolve(),
        counts,
        results,
    )

    correct = sum(result.correct for result in results)
    print(f"统计完成：总数 {len(results)}，定位正确 {correct}，定位有问题 {len(results) - correct}")


if __name__ == "__main__":
    main()
