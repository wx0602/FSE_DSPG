#!/usr/bin/env python3
"""Count whether localization was correct by intersecting the files a patch
modifies with the files the baseline patch modifies."""

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
            return "missing baseline patch with the same name"
        if not self.generated_files:
            return "generated patch yielded no modified files"
        if not self.baseline_files:
            return "baseline patch yielded no modified files"
        return "generated_patch_and_baseline_modify_disjoint_files"


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
    """Extract repository-relative paths from diff --git, --- and +++ headers."""
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
    output = output_dir / "localization_stats_summary.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "method",
                "patch_total_count",
                "localization_correct_count",
                "localization_error_count",
                "accuracy",
                "error_rate",
            ]
        )
        total_count = sum(total for _, total, _, _ in counts)
        total_correct = sum(correct for _, _, correct, _ in counts)
        total_error = sum(error for _, _, _, error in counts)
        for method, total, correct, error in counts:
            writer.writerow(
                [
                    method,
                    total,
                    correct,
                    error,
                    f"{correct / total:.2%}" if total else "0.00%",
                    f"{error / total:.2%}" if total else "0.00%",
                ]
            )
        writer.writerow(
            [
                "total",
                total_count,
                total_correct,
                total_error,
                f"{total_correct / total_count:.2%}" if total_count else "0.00%",
                f"{total_error / total_count:.2%}" if total_count else "0.00%",
            ]
        )