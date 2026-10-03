#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path


def count_occurrences_in_text(text: str, needle: str) -> int:
    """Count occurrences of a substring, allowing overlapping matches."""
    if not needle:
        return 0

    count = 0
    start = 0
    while True:
        idx = text.find(needle, start)
        if idx == -1:
            break
        count += 1
        start = idx + 1
    return count


def count_occurrences_in_dir(directory: Path, needle: str) -> int:
    """Recursively count string occurrences in all files under a directory."""
    if not directory.exists() or not directory.is_dir():
        return 0

    total = 0
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                total += count_occurrences_in_text(content, needle)
            except Exception as e:
                print(f"[WARN] Failed to read file: {file_path}, error={e}", file=sys.stderr)
    return total


def run_maven_test(repo_path: Path) -> str:
    """Run mvn clean test in the specified repository and return full console output."""
    cmd = ["mvn", "clean", "test"]
    print(f"[INFO] Starting command: {' '.join(cmd)}")
    print(f"[INFO] Repository path: {repo_path}")

    process = subprocess.run(
        cmd,
        cwd=str(repo_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    output = process.stdout or ""

    print(f"[INFO] mvn clean test finished, return code: {process.returncode}")
    return output


def append_to_csv(csv_path: Path, row: list, header: list) -> None:
    """Append row to CSV. Write header if file does not exist."""
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)


def print_table(header: list, row: list) -> None:
    """Print results as a simple table in the console."""
    widths = [len(str(h)) for h in header]
    for i, cell in enumerate(row):
        widths[i] = max(widths[i], len(str(cell)))

    def format_row(items):
        return "| " + " | ".join(str(item).ljust(widths[i]) for i, item in enumerate(items)) + " |"

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"

    print("\nResults:")
    print(sep)
    print(format_row(header))
    print(sep)
    print(format_row(row))
    print(sep)


def main():
    parser = argparse.ArgumentParser(
        description="Run Maven tests, count key strings in surefire reports and console output, append results to result.csv"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Path to Java Maven repository"
    )
    parser.add_argument(
        "--poc_string",
        required=True,
        help="String to count in target/surefire-reports test result files"
    )
    parser.add_argument(
        "--poc_cmd",
        default="poc_cmd",
        help='String printed in console during test, default: "poc_cmd"'
    )
    parser.add_argument(
        "--csv",
        default="result.csv",
        help="Output CSV file path, default: result.csv"
    )

    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"[ERROR] Repo path does not exist or is not a directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    repo_name = repo_path.name
    poc_string = args.poc_string
    poc_cmd = args.poc_cmd
    csv_path = Path(args.csv).resolve()

    # 1. Run mvn clean test
    console_output = run_maven_test(repo_path)

    # 2. Count poc_cmd occurrences in console output
    poc_cmd_count = count_occurrences_in_text(console_output, poc_cmd)

    # 3. Count poc_string occurrences in surefire reports
    surefire_dir = repo_path / "target" / "surefire-reports"
    poc_string_count = count_occurrences_in_dir(surefire_dir, poc_string)

    # 4. Print results
    print(f"\nrepo_name   : {repo_name}")
    print(f"poc_string  : {poc_string}")
    print(f"poc_str_cnt : {poc_string_count}")
    print(f"poc_cmd     : {poc_cmd}")
    print(f"poc_cmd_cnt : {poc_cmd_count}")

    # 5. Append to CSV
    header = ["repo_name", "poc_string", "poc_string_count", "poc_cmd", "poc_cmd_count"]
    row = [repo_name, poc_string, poc_string_count, poc_cmd, poc_cmd_count]
    append_to_csv(csv_path, row, header)

    print(f"\n[INFO] Results appended to: {csv_path}")

    # 6. Print table in console
    print_table(header, row)


if __name__ == "__main__":
    main()

