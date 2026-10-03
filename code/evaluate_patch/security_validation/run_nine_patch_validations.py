#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Run the baseline, nine patch validations, and nine comparisons sequentially."""

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


EXPECTED_TASK_COUNT = 63
EXPECTED_PATCH_DIR_COUNT = 9
DEFAULT_REPO_ROOT = Path(
    "/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816"
)
DEFAULT_PATCHES_ROOT = Path(
    "/media/wql/办公/AVR_agent/7月实验结果验证/"
    "CVE 描述验证结果/正则化的补丁"
)


class PipelineError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parser = argparse.ArgumentParser(
        description=(
            "Sequentially validate the 63 vulnerable baselines, then run the "
            "multi-patch validator and comparison for each of nine patch directories."
        )
    )
    parser.add_argument("--yaml", default=str(script_dir / "vuls-test.yaml"))
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--patches-root", default=str(DEFAULT_PATCHES_ROOT))
    parser.add_argument(
        "--output-root",
        default=str(script_dir / f"nine_patch_validation_{timestamp}"),
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--mvn", default="mvn")
    parser.add_argument("--git", default="git")
    parser.add_argument(
        "--keep-workdirs",
        action="store_true",
        help="Keep temporary repositories created by the multi-patch validator",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_tasks(yaml_path: Path) -> list[dict]:
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list):
        raise PipelineError("YAML must contain a list at key 'tasks'")
    if not all(isinstance(task, dict) for task in tasks):
        raise PipelineError("Every YAML task must be a mapping")
    return tasks


def discover_patch_dirs(patches_root: Path) -> list[Path]:
    return sorted(path for path in patches_root.iterdir() if path.is_dir())


def preflight(
    yaml_path: Path,
    repo_root: Path,
    patches_root: Path,
) -> tuple[list[dict], list[Path]]:
    if not yaml_path.is_file():
        raise PipelineError(f"YAML not found: {yaml_path}")
    if not repo_root.is_dir():
        raise PipelineError(f"Repository root not found: {repo_root}")
    if not patches_root.is_dir():
        raise PipelineError(f"Patch root not found: {patches_root}")

    tasks = load_tasks(yaml_path)
    if len(tasks) != EXPECTED_TASK_COUNT:
        raise PipelineError(
            f"Expected {EXPECTED_TASK_COUNT} YAML tasks, found {len(tasks)}"
        )

    target_ids = [str(task.get("target_id") or "") for task in tasks]
    if any(not target_id for target_id in target_ids):
        raise PipelineError("At least one YAML task is missing target_id")
    if len(set(target_ids)) != len(target_ids):
        raise PipelineError("Duplicate target_id values exist in YAML")

    missing_repos = [
        target_id for target_id in target_ids if not (repo_root / target_id).is_dir()
    ]
    if missing_repos:
        raise PipelineError(
            "Repositories missing for YAML targets: " + ", ".join(missing_repos)
        )

    patch_dirs = discover_patch_dirs(patches_root)
    if len(patch_dirs) != EXPECTED_PATCH_DIR_COUNT:
        raise PipelineError(
            f"Expected {EXPECTED_PATCH_DIR_COUNT} patch directories under "
            f"{patches_root}, found {len(patch_dirs)}"
        )

    empty_patch_dirs = [
        path.name for path in patch_dirs if not any(path.rglob("*.patch"))
    ]
    if empty_patch_dirs:
        raise PipelineError(
            "Patch directories containing no .patch files: "
            + ", ".join(empty_patch_dirs)
        )

    return tasks, patch_dirs


def run_and_tee(cmd: list[str], cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command_text = shlex.join(cmd)
    print(f"\n[COMMAND] {command_text}", flush=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"[COMMAND] {command_text}\n")
        log_file.flush()
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log_file.write(line)
        return process.wait()


def index_summary(summary: dict) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    details = summary.get("details")
    if not isinstance(details, dict):
        return indexed
    for status, items in details.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("target_id"):
                continue
            normalized = dict(item)
            normalized["status"] = status
            indexed[str(item["target_id"])] = normalized
    return indexed


def metrics_of(item: dict) -> dict:
    metrics = item.get("metrics")
    return metrics if isinstance(metrics, dict) else {}


def validate_baseline(summary_path: Path, expected_ids: set[str], run_number: int) -> dict:
    if not summary_path.is_file():
        raise PipelineError(f"Baseline summary not produced: {summary_path}")

    summary = load_json(summary_path)
    indexed = index_summary(summary)
    counts = summary.get("counts") or {}
    vulnerable_ids = {
        target_id
        for target_id, item in indexed.items()
        if item.get("status") == "VULNERABLE"
        and bool(metrics_of(item).get("compile_ok"))
        and int(metrics_of(item).get("match_count", 0) or 0) > 0
    }
    missing_ids = sorted(expected_ids - set(indexed))
    not_vulnerable_ids = sorted(expected_ids - vulnerable_ids)
    all_vulnerable = (
        len(indexed) == EXPECTED_TASK_COUNT
        and vulnerable_ids == expected_ids
        and not missing_ids
    )

    result = {
        "run_number": run_number,
        "all_63_vulnerable": all_vulnerable,
        "indexed_targets": len(indexed),
        "vulnerable_targets": len(vulnerable_ids),
        "counts": counts,
        "missing_targets": missing_ids,
        "not_vulnerable_targets": not_vulnerable_ids,
        "summary": str(summary_path),
    }

    print("\n" + "=" * 80)
    print(f"[BASELINE {run_number}] 63 ORIGINAL REPOSITORIES")
    print(f"VULNERABLE:      {len(vulnerable_ids)}/{EXPECTED_TASK_COUNT}")
    print(f"NOT_VULNERABLE:  {int(counts.get('NOT_VULNERABLE', 0) or 0)}")
    print(f"COMPILE_FAILED:  {int(counts.get('COMPILE_FAILED', 0) or 0)}")
    print(f"ERROR:           {int(counts.get('ERROR', 0) or 0)}")
    print(f"ALL_VULNERABLE:  {all_vulnerable}")
    if not_vulnerable_ids:
        print("NOT_CONFIRMED_VULNERABLE:")
        for target_id in not_vulnerable_ids:
            print(f"  - {target_id}")
    print("=" * 80, flush=True)

    return result


def calculate_comparison(baseline_path: Path, patched_path: Path) -> dict:
    baseline = index_summary(load_json(baseline_path))
    patched = index_summary(load_json(patched_path))
    lowered: list[str] = []
    no_vulnerability: list[str] = []
    comparable: list[str] = []

    for target_id, right_item in sorted(patched.items()):
        left_item = baseline.get(target_id)
        if left_item is None:
            continue
        left_metrics = metrics_of(left_item)
        right_metrics = metrics_of(right_item)
        if not bool(left_metrics.get("compile_ok")):
            continue
        if not bool(right_metrics.get("compile_ok")):
            continue
        if left_item.get("mode") != right_item.get("mode"):
            continue

        comparable.append(target_id)
        left_count = int(left_metrics.get("match_count", 0) or 0)
        right_count = int(right_metrics.get("match_count", 0) or 0)
        if right_count < left_count:
            lowered.append(target_id)
        if (
            left_item.get("status") == "VULNERABLE"
            and left_count > 0
            and right_item.get("status") == "NOT_VULNERABLE"
            and right_count == 0
        ):
            no_vulnerability.append(target_id)

    return {
        "comparable_count": len(comparable),
        "lowered_count": len(lowered),
        "no_vulnerability_count": len(no_vulnerability),
        "lowered_targets": lowered,
        "no_vulnerability_targets": no_vulnerability,
    }


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    yaml_path = Path(args.yaml).resolve()
    repo_root = Path(args.repo_root).resolve()
    patches_root = Path(args.patches_root).resolve()
    output_root = Path(args.output_root).resolve()

    try:
        tasks, patch_dirs = preflight(yaml_path, repo_root, patches_root)
        expected_ids = {str(task["target_id"]) for task in tasks}
        output_root.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] YAML tasks: {len(tasks)}")
        print(f"[INFO] Patch directories: {len(patch_dirs)}")
        for index, patch_dir in enumerate(patch_dirs, start=1):
            patch_count = sum(1 for _ in patch_dir.rglob("*.patch"))
            print(f"  {index}. {patch_dir.name}: {patch_count} patch file(s)")
        print(f"[INFO] Output root: {output_root}", flush=True)

        pipeline_summary: dict = {
            "yaml": str(yaml_path),
            "repo_root": str(repo_root),
            "patches_root": str(patches_root),
            "output_root": str(output_root),
            "expected_task_count": EXPECTED_TASK_COUNT,
            "baseline_runs": [],
            "patch_runs": [],
        }
        active_baseline_dir: Path | None = None
        active_baseline_run: int | None = None

        for run_number, patch_dir in enumerate(patch_dirs, start=1):
            round_dir = output_root / f"{run_number:02d}_{patch_dir.name}"
            round_dir.mkdir(parents=True, exist_ok=True)

            if run_number in (1, EXPECTED_PATCH_DIR_COUNT):
                active_baseline_dir = output_root / f"baseline_run_{run_number:02d}"
                active_baseline_run = run_number
                baseline_cmd = [
                    args.python,
                    str(script_dir / "origin_vuls_Dtest_count.py"),
                    "--yaml",
                    str(yaml_path),
                    "--repo_root",
                    str(repo_root),
                    "--out_dir",
                    str(active_baseline_dir),
                    "--timeout",
                    str(args.timeout),
                    "--mvn",
                    args.mvn,
                    "--workers",
                    "1",
                ]
                baseline_returncode = run_and_tee(
                    baseline_cmd,
                    script_dir,
                    active_baseline_dir / "runner.log",
                )
                baseline_result = validate_baseline(
                    active_baseline_dir / "summary.json",
                    expected_ids,
                    run_number,
                )
                baseline_result["returncode"] = baseline_returncode
                pipeline_summary["baseline_runs"].append(baseline_result)

            if active_baseline_dir is None:
                raise PipelineError("No active baseline summary is available")
            if active_baseline_run is None:
                raise PipelineError("No active baseline run number is available")

            patched_dir = round_dir / "patched"
            multi_cmd = [
                args.python,
                str(script_dir / "origin_vuls_multi_patch_best_count.py"),
                "--yaml",
                str(yaml_path),
                "--repo_root",
                str(repo_root),
                "--patch_root",
                str(patch_dir),
                "--out_dir",
                str(patched_dir),
                "--work_root",
                str(round_dir / "workdirs"),
                "--timeout",
                str(args.timeout),
                "--mvn",
                args.mvn,
                "--git",
                args.git,
                "--jobs",
                "1",
            ]
            if args.keep_workdirs:
                multi_cmd.append("--keep_workdirs")
            multi_returncode = run_and_tee(
                multi_cmd,
                script_dir,
                round_dir / "multi_patch_runner.log",
            )
            patched_summary_path = patched_dir / "summary.json"
            if multi_returncode != 0 or not patched_summary_path.is_file():
                raise PipelineError(
                    f"Multi-patch run {run_number} failed with return code "
                    f"{multi_returncode}: {patch_dir.name}"
                )

            compare_cmd = [
                args.python,
                str(script_dir / "compare_compiled_success_poc_counts_compat.py"),
                str(active_baseline_dir),
                str(patched_dir),
                "--left-label",
                f"baseline_{active_baseline_run:02d}",
                "--right-label",
                patch_dir.name,
                "--show-skipped",
            ]
            compare_returncode = run_and_tee(
                compare_cmd,
                script_dir,
                round_dir / "comparison.txt",
            )
            if compare_returncode != 0:
                raise PipelineError(
                    f"Comparison run {run_number} failed with return code "
                    f"{compare_returncode}: {patch_dir.name}"
                )

            comparison = calculate_comparison(
                active_baseline_dir / "summary.json",
                patched_summary_path,
            )
            patched_summary = load_json(patched_summary_path)
            patch_count = sum(1 for _ in patch_dir.rglob("*.patch"))
            round_result = {
                "run_number": run_number,
                "patch_directory": patch_dir.name,
                "patch_root": str(patch_dir),
                "patch_file_count": patch_count,
                "baseline_summary": str(active_baseline_dir / "summary.json"),
                "patched_summary": str(patched_summary_path),
                "comparison_log": str(round_dir / "comparison.txt"),
                "multi_patch_returncode": multi_returncode,
                "comparison_returncode": compare_returncode,
                "patched_status_counts": patched_summary.get("counts") or {},
                **comparison,
            }
            pipeline_summary["patch_runs"].append(round_result)

            print("\n" + "#" * 80)
            print(f"[ROUND {run_number}/9] {patch_dir.name}")
            print(f"PATCH FILES:          {patch_count}")
            print(f"COMPARABLE:           {comparison['comparable_count']}")
            print(f"MATCH COUNT LOWERED:  {comparison['lowered_count']}")
            print(
                "NO VULNERABILITY:      "
                f"{comparison['no_vulnerability_count']}"
            )
            print("#" * 80, flush=True)

            (output_root / "pipeline_summary.json").write_text(
                json.dumps(pipeline_summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        for result in pipeline_summary["patch_runs"]:
            print(
                f"{result['run_number']:02d}. {result['patch_directory']}: "
                f"lowered={result['lowered_count']}, "
                f"no_vulnerability={result['no_vulnerability_count']}"
            )
        baseline_checks_ok = all(
            result.get("all_63_vulnerable", False)
            for result in pipeline_summary["baseline_runs"]
        )
        print(f"Both baseline checks passed: {baseline_checks_ok}")
        print(f"Summary: {output_root / 'pipeline_summary.json'}")
        print("=" * 80)
        return 0 if baseline_checks_ok else 2
    except (PipelineError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FATAL] {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
