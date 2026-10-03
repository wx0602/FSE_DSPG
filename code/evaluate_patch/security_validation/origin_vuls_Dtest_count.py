#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch runner for validating vulnerable behavior on original downstream repos.

This script is intentionally similar to origin_vuls_Dtest.py, but extends the
output with count-oriented statistics:

1. Per-task detection details now include counts.
   - poc_string / poc_string2 / poc_cmd: substring occurrence count
   - poc_file: existence flag plus file count (0 or 1)
   - poc_exit: match flag plus match count (0 or 1)

2. summary.json includes extra aggregate statistics.
   - detection_mode_counts: number of tasks using each detection mode
   - detection_field_counts: number of tasks defining each poc_* field
   - matched_content_total_counts: accumulated per-task match counts by mode

3. Before running the PoC test, the script performs a build precheck:
   - first: mvn clean install -DskipTests
   - fallback: mvn clean install -Dmaven.test.skip=true
   - only if both fail, status becomes COMPILE_FAILED

Typical repo layout for this script:
- /path/to/resource/<target_id>
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


DETECTION_FIELDS = ["poc_string", "poc_file", "poc_exit", "poc_string2", "poc_cmd"]
DETECTION_MODES = ["poc_string", "poc_file", "poc_exit", "poc_string2", "poc_cmd"]
PRIMARY_PRECHECK_ARGS = ["clean", "install", "-DskipTests"]
FALLBACK_PRECHECK_ARGS = ["clean", "install", "-Dmaven.test.skip=true"]


def detect_mode(task: dict) -> str:
    """Return the active detection mode and enforce mutual exclusivity."""
    has_poc_file = task.get("poc_file") is not None
    has_poc_exit = task.get("poc_exit") is not None
    has_poc_string2 = task.get("poc_string2") is not None
    has_poc_cmd = task.get("poc_cmd") is not None

    enabled = [
        name
        for name, on in [
            ("poc_file", has_poc_file),
            ("poc_exit", has_poc_exit),
            ("poc_string2", has_poc_string2),
            ("poc_cmd", has_poc_cmd),
        ]
        if on
    ]

    if len(enabled) > 1:
        raise ValueError(
            "Only one mode allowed among poc_file/poc_exit/poc_string2/poc_cmd. "
            f"Got: {enabled}"
        )

    if has_poc_file:
        return "poc_file"
    if has_poc_exit:
        return "poc_exit"
    if has_poc_string2:
        return "poc_string2"
    if has_poc_cmd:
        return "poc_cmd"
    return "poc_string"


def resolve_repo_path(repo_root: Path, target_id: str) -> Path:
    return (repo_root / target_id).resolve()


def resolve_module_path(repo_path: Path, module: str) -> Path:
    module = module or "."
    return (repo_path / module).resolve()


def resolve_poc_file_path(exec_dir: Path, poc_file: str | None) -> Path | None:
    if poc_file is None:
        return None

    raw = Path(str(poc_file))
    if raw.is_absolute():
        return raw
    return (exec_dir / raw).resolve()


def cleanup_poc_file(poc_file_path: Path | None) -> tuple[bool, str]:
    if poc_file_path is None:
        return True, ""

    if not poc_file_path.exists():
        return True, ""

    if poc_file_path.is_dir():
        return False, f"poc_file path exists and is a directory: {poc_file_path}"

    try:
        poc_file_path.unlink()
    except Exception as exc:
        return False, f"failed to remove existing poc_file {poc_file_path}: {exc}"

    return True, ""


def collect_surefire_reports(exec_dir: Path) -> tuple[str, list[str]]:
    """
    Collect surefire report content for detection.

    Some projects only expose the interesting exception text in
    target/surefire-reports rather than Maven stdout/stderr.
    """
    reports_dir = exec_dir / "target" / "surefire-reports"
    if not reports_dir.is_dir():
        return "", []

    content_parts = []
    collected_files = []
    patterns = ("*.txt", "*.xml", "*.dump", "*.dumpstream")

    for pattern in patterns:
        for path in sorted(reports_dir.glob(pattern)):
            if not path.is_file():
                continue
            collected_files.append(str(path))
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                text = f"[ERROR] failed to read report {path}: {exc}"
            content_parts.append(f"===== REPORT: {path.name} =====\n{text}")

    return "\n\n".join(content_parts), collected_files


def count_occurrences(haystack: str, needle: str) -> int:
    if not needle:
        return 0
    return haystack.casefold().count(needle.casefold())


def evaluate_detection(
    mode: str,
    task: dict,
    combined_output: str,
    returncode: int,
    poc_file_path: Path | None,
) -> tuple[bool, str, dict]:
    if mode == "poc_file":
        if poc_file_path is None:
            metrics = {"mode": mode, "match_count": 0, "exists": False}
            return False, "poc_file mode selected but path is missing; file_count=0", metrics
        matched = poc_file_path.exists()
        file_count = 1 if matched else 0
        metrics = {
            "mode": mode,
            "match_count": file_count,
            "exists": matched,
            "poc_file_path": str(poc_file_path),
        }
        info = f"poc_file exists={matched}: {poc_file_path}; file_count={file_count}"
        return matched, info, metrics

    if mode == "poc_exit":
        expected = int(task["poc_exit"])
        matched = returncode == expected
        match_count = 1 if matched else 0
        metrics = {
            "mode": mode,
            "match_count": match_count,
            "expected_exit": expected,
        }
        info = (
            f"returncode={returncode}, expected={expected}, "
            f"exit_match_count={match_count}"
        )
        return matched, info, metrics

    if mode == "poc_string2":
        expected = str(task["poc_string2"])
        occurrence_count = count_occurrences(combined_output, expected)
        matched = occurrence_count > 0
        metrics = {
            "mode": mode,
            "match_count": occurrence_count,
            "expected": expected,
        }
        info = (
            f"poc_string2 matched={matched} (case-insensitive): {expected!r}; "
            f"occurrence_count={occurrence_count}"
        )
        return matched, info, metrics

    if mode == "poc_cmd":
        expected = str(task["poc_cmd"])
        occurrence_count = count_occurrences(combined_output, expected)
        matched = occurrence_count > 0
        metrics = {
            "mode": mode,
            "match_count": occurrence_count,
            "expected": expected,
        }
        info = (
            f"poc_cmd matched={matched} (case-insensitive): {expected!r}; "
            f"occurrence_count={occurrence_count}"
        )
        return matched, info, metrics

    expected = task.get("poc_string")
    if expected is None:
        metrics = {"mode": mode, "match_count": 0}
        return False, "poc_string mode selected but poc_string is missing", metrics

    expected = str(expected)
    occurrence_count = count_occurrences(combined_output, expected)
    matched = occurrence_count > 0
    metrics = {
        "mode": mode,
        "match_count": occurrence_count,
        "expected": expected,
    }
    info = (
        f"poc_string matched={matched} (case-insensitive): {expected!r}; "
        f"occurrence_count={occurrence_count}"
    )
    return matched, info, metrics


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    timeout_sec: int,
) -> dict:
    result = {
        "stdout": "",
        "stderr": "",
        "returncode": -1,
        "timeout": False,
        "error": None,
    }

    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
        result["stdout"] = completed.stdout or ""
        result["stderr"] = completed.stderr or ""
        result["returncode"] = completed.returncode
        return result
    except subprocess.TimeoutExpired as exc:
        result["stdout"] = exc.stdout or ""
        result["stderr"] = (
            (exc.stderr or "")
            + f"\n[ERROR] timeout after {timeout_sec} seconds; command timed out"
        )
        result["timeout"] = True
        result["returncode"] = -1
        return result
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result


def run_compile_precheck(
    mvn_bin: str,
    *,
    cwd: Path,
    timeout_sec: int,
) -> dict:
    attempts = []

    for label, tail_args in [
        ("primary", PRIMARY_PRECHECK_ARGS),
        ("fallback", FALLBACK_PRECHECK_ARGS),
    ]:
        cmd = [mvn_bin, *tail_args]
        result = run_command(cmd, cwd=cwd, timeout_sec=timeout_sec)
        attempt = {
            "label": label,
            "cmd": cmd,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
            "timeout": result["timeout"],
            "error": result["error"],
            "success": result["error"] is None and result["returncode"] == 0,
        }
        attempts.append(attempt)
        if attempt["success"]:
            break

    success_attempt = next((attempt for attempt in attempts if attempt["success"]), None)
    chosen_attempt = success_attempt or attempts[-1]

    return {
        "attempts": attempts,
        "success": success_attempt is not None,
        "used_fallback": len(attempts) > 1,
        "chosen_attempt": chosen_attempt,
    }


def write_task_log(
    log_path: Path,
    *,
    target_id: str,
    repo_path: Path,
    exec_dir: Path,
    module: str,
    dtest: str,
    mode: str,
    compile_attempts: list[dict],
    test_command: list[str],
    start_time: str,
    end_time: str,
    compile_returncode: int,
    compile_timeout: bool,
    test_returncode: int,
    test_timeout: bool,
    detection_info: str,
    detection_metrics: dict,
    status: str,
    test_stdout: str,
    test_stderr: str,
    poc_file_path: Path | None,
    surefire_files: list[str],
    surefire_text: str,
) -> None:
    lines = [
        f"target_id: {target_id}",
        f"repo_path: {repo_path}",
        f"exec_dir: {exec_dir}",
        f"module: {module}",
        f"Dtest: {dtest}",
        f"mode: {mode}",
        f"test_command: {' '.join(test_command)}",
        f"start_time: {start_time}",
        f"end_time: {end_time}",
        f"compile_returncode: {compile_returncode}",
        f"compile_timeout: {compile_timeout}",
        f"test_returncode: {test_returncode}",
        f"test_timeout: {test_timeout}",
        f"status: {status}",
        f"detection: {detection_info}",
        f"detection_metrics: {json.dumps(detection_metrics, ensure_ascii=False)}",
    ]

    for idx, attempt in enumerate(compile_attempts, start=1):
        lines.extend(
            [
                f"compile_attempt_{idx}_label: {attempt['label']}",
                f"compile_attempt_{idx}_command: {' '.join(attempt['cmd'])}",
                f"compile_attempt_{idx}_returncode: {attempt['returncode']}",
                f"compile_attempt_{idx}_timeout: {attempt['timeout']}",
                f"compile_attempt_{idx}_error: {attempt['error']}",
                f"compile_attempt_{idx}_success: {attempt['success']}",
            ]
        )

    if poc_file_path is not None:
        lines.append(f"poc_file_path: {poc_file_path}")
    if surefire_files:
        lines.append("surefire_files:")
        lines.extend(surefire_files)

    for idx, attempt in enumerate(compile_attempts, start=1):
        lines.extend(
            [
                "",
                f"===== COMPILE ATTEMPT {idx} STDOUT =====",
                attempt["stdout"] or "",
                "",
                f"===== COMPILE ATTEMPT {idx} STDERR =====",
                attempt["stderr"] or "",
            ]
        )

    lines.extend(
        [
            "",
            "===== TEST STDOUT =====",
            test_stdout or "",
            "",
            "===== TEST STDERR =====",
            test_stderr or "",
        ]
    )

    if surefire_text:
        lines.extend(
            [
                "",
                "===== SUREFIRE REPORTS =====",
                surefire_text,
            ]
        )

    log_path.write_text("\n".join(lines), encoding="utf-8")


def init_summary_counters() -> dict:
    return {
        "detection_mode_counts": {key: 0 for key in DETECTION_MODES},
        "detection_field_counts": {key: 0 for key in DETECTION_FIELDS},
        "matched_content_total_counts": {key: 0 for key in DETECTION_MODES},
    }


def update_summary_counters(summary_counters: dict, task: dict, mode: str, metrics: dict) -> None:
    summary_counters["detection_mode_counts"][mode] += 1

    for field in DETECTION_FIELDS:
        if task.get(field) is not None:
            summary_counters["detection_field_counts"][field] += 1

    match_count = int(metrics.get("match_count", 0) or 0)
    summary_counters["matched_content_total_counts"][mode] += match_count


def write_summary_csv(csv_path: Path, summary: dict) -> None:
    fieldnames = [
        "status",
        "target_id",
        "mode",
        "info",
        "compile_ok",
        "compile_attempts",
        "compile_fallback_used",
        "compile_strategy",
        "compile_returncode",
        "compile_timeout",
        "test_returncode",
        "test_timeout",
        "match_count",
        "expected",
        "exists",
        "poc_file_path",
        "expected_exit",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for status in ["VULNERABLE", "NOT_VULNERABLE", "COMPILE_FAILED", "ERROR"]:
            for item in summary["details"].get(status, []):
                metrics = item.get("metrics", {}) or {}
                writer.writerow(
                    {
                        "status": status,
                        "target_id": item.get("target_id"),
                        "mode": item.get("mode"),
                        "info": item.get("info"),
                        "compile_ok": metrics.get("compile_ok"),
                        "compile_attempts": metrics.get("compile_attempts"),
                        "compile_fallback_used": metrics.get("compile_fallback_used"),
                        "compile_strategy": metrics.get("compile_strategy"),
                        "compile_returncode": metrics.get("compile_returncode"),
                        "compile_timeout": metrics.get("compile_timeout"),
                        "test_returncode": metrics.get("test_returncode"),
                        "test_timeout": metrics.get("test_timeout"),
                        "match_count": metrics.get("match_count"),
                        "expected": metrics.get("expected"),
                        "exists": metrics.get("exists"),
                        "poc_file_path": metrics.get("poc_file_path"),
                        "expected_exit": metrics.get("expected_exit"),
                    }
                )


def run_one_task(
    mvn_bin: str,
    repo_root: Path,
    out_dir: Path,
    timeout_sec: int,
    task: dict,
):
    target_id = task.get("target_id")
    if not target_id:
        return ("ERROR", None, "missing target_id", None, None)

    module = task.get("module", ".")
    dtest = task.get("Dtest")
    if not dtest:
        return ("ERROR", target_id, "missing Dtest", None, None)

    try:
        mode = detect_mode(task)
    except Exception as exc:
        return ("ERROR", target_id, str(exc), None, None)

    repo_path = resolve_repo_path(repo_root, target_id)
    exec_dir = resolve_module_path(repo_path, module)

    if not repo_path.is_dir():
        return ("ERROR", target_id, f"repo not found: {repo_path}", mode, None)
    if not exec_dir.is_dir():
        return ("ERROR", target_id, f"module dir not found: {exec_dir}", mode, None)

    poc_file_path = resolve_poc_file_path(exec_dir, task.get("poc_file"))
    ok, cleanup_info = cleanup_poc_file(poc_file_path)
    if not ok:
        return ("ERROR", target_id, cleanup_info, mode, None)

    primary_compile_cmd = [mvn_bin, *PRIMARY_PRECHECK_ARGS]
    fallback_compile_cmd = [mvn_bin, *FALLBACK_PRECHECK_ARGS]
    test_cmd = [mvn_bin, "clean", "test", f"-Dtest={dtest}"]

    print("\n" + "=" * 80)
    print(f"[TASK] target_id={target_id}")
    print(f"[INFO] repo     = {repo_path}")
    print(f"[INFO] module   = {module}")
    print(f"[INFO] exec_dir = {exec_dir}")
    print(f"[INFO] Dtest    = {dtest}")
    print(f"[INFO] mode     = {mode}")
    if poc_file_path is not None:
        print(f"[INFO] poc_file = {poc_file_path}")
    if mode == "poc_exit":
        print(f"[INFO] poc_exit = {task.get('poc_exit')}")
    if mode == "poc_cmd":
        print(f"[INFO] poc_cmd  = {task.get('poc_cmd')}")
    if mode == "poc_string2":
        print(f"[INFO] poc_str2 = {task.get('poc_string2')}")
    if mode == "poc_string":
        print(f"[INFO] poc_str  = {task.get('poc_string')}")
    print(f"[INFO] precheck1 = {' '.join(primary_compile_cmd)}")
    print(f"[INFO] precheck2 = {' '.join(fallback_compile_cmd)}")
    print(f"[INFO] test     = {' '.join(test_cmd)}")
    print("=" * 80)

    start_time = datetime.now().isoformat(timespec="seconds")
    compile_precheck = run_compile_precheck(
        mvn_bin,
        cwd=exec_dir,
        timeout_sec=timeout_sec,
    )
    compile_attempts = compile_precheck["attempts"]
    chosen_compile = compile_precheck["chosen_attempt"]

    if chosen_compile["error"] is not None and not compile_precheck["success"]:
        end_time = datetime.now().isoformat(timespec="seconds")
        log_path = out_dir / "logs" / f"{target_id}.log"
        detection_metrics = {
            "mode": mode,
            "match_count": 0,
            "compile_ok": False,
            "compile_attempts": len(compile_attempts),
            "compile_fallback_used": compile_precheck["used_fallback"],
            "compile_strategy": chosen_compile["label"],
            "compile_returncode": -1,
            "compile_timeout": False,
            "test_returncode": -1,
            "test_timeout": False,
        }
        detection_info = f"compile execution error: {chosen_compile['error']}"
        write_task_log(
            log_path,
            target_id=target_id,
            repo_path=repo_path,
            exec_dir=exec_dir,
            module=str(module),
            dtest=str(dtest),
            mode=mode,
            compile_attempts=compile_attempts,
            test_command=test_cmd,
            start_time=start_time,
            end_time=end_time,
            compile_returncode=-1,
            compile_timeout=False,
            test_returncode=-1,
            test_timeout=False,
            detection_info=detection_info,
            detection_metrics=detection_metrics,
            status="ERROR",
            test_stdout="",
            test_stderr="",
            poc_file_path=poc_file_path,
            surefire_files=[],
            surefire_text="",
        )
        return ("ERROR", target_id, detection_info, mode, detection_metrics)

    if not compile_precheck["success"]:
        end_time = datetime.now().isoformat(timespec="seconds")
        log_path = out_dir / "logs" / f"{target_id}.log"
        detection_metrics = {
            "mode": mode,
            "match_count": 0,
            "compile_ok": False,
            "compile_attempts": len(compile_attempts),
            "compile_fallback_used": compile_precheck["used_fallback"],
            "compile_strategy": chosen_compile["label"],
            "compile_returncode": chosen_compile["returncode"],
            "compile_timeout": chosen_compile["timeout"],
            "test_returncode": -1,
            "test_timeout": False,
        }
        primary_attempt = compile_attempts[0]
        detection_info = (
            "compile failed after fallback: "
            f"primary_returncode={primary_attempt['returncode']}, "
            f"primary_timeout={primary_attempt['timeout']}, "
            f"fallback_returncode={chosen_compile['returncode']}, "
            f"fallback_timeout={chosen_compile['timeout']}"
        )
        write_task_log(
            log_path,
            target_id=target_id,
            repo_path=repo_path,
            exec_dir=exec_dir,
            module=str(module),
            dtest=str(dtest),
            mode=mode,
            compile_attempts=compile_attempts,
            test_command=test_cmd,
            start_time=start_time,
            end_time=end_time,
            compile_returncode=chosen_compile["returncode"],
            compile_timeout=chosen_compile["timeout"],
            test_returncode=-1,
            test_timeout=False,
            detection_info=detection_info,
            detection_metrics=detection_metrics,
            status="COMPILE_FAILED",
            test_stdout="",
            test_stderr="",
            poc_file_path=poc_file_path,
            surefire_files=[],
            surefire_text="",
        )
        return ("COMPILE_FAILED", target_id, detection_info, mode, detection_metrics)

    test_result = run_command(test_cmd, cwd=exec_dir, timeout_sec=timeout_sec)
    if test_result["error"] is not None:
        end_time = datetime.now().isoformat(timespec="seconds")
        log_path = out_dir / "logs" / f"{target_id}.log"
        detection_metrics = {
            "mode": mode,
            "match_count": 0,
            "compile_ok": True,
            "compile_attempts": len(compile_attempts),
            "compile_fallback_used": compile_precheck["used_fallback"],
            "compile_strategy": chosen_compile["label"],
            "compile_returncode": chosen_compile["returncode"],
            "compile_timeout": chosen_compile["timeout"],
            "test_returncode": -1,
            "test_timeout": False,
        }
        detection_info = f"test execution error: {test_result['error']}"
        write_task_log(
            log_path,
            target_id=target_id,
            repo_path=repo_path,
            exec_dir=exec_dir,
            module=str(module),
            dtest=str(dtest),
            mode=mode,
            compile_attempts=compile_attempts,
            test_command=test_cmd,
            start_time=start_time,
            end_time=end_time,
            compile_returncode=chosen_compile["returncode"],
            compile_timeout=chosen_compile["timeout"],
            test_returncode=-1,
            test_timeout=False,
            detection_info=detection_info,
            detection_metrics=detection_metrics,
            status="ERROR",
            test_stdout="",
            test_stderr=test_result["error"],
            poc_file_path=poc_file_path,
            surefire_files=[],
            surefire_text="",
        )
        return ("ERROR", target_id, detection_info, mode, detection_metrics)

    end_time = datetime.now().isoformat(timespec="seconds")
    surefire_text, surefire_files = collect_surefire_reports(exec_dir)
    combined_output = f"{test_result['stdout']}\n{test_result['stderr']}\n{surefire_text}"
    matched, detection_info, detection_metrics = evaluate_detection(
        mode=mode,
        task=task,
        combined_output=combined_output,
        returncode=test_result["returncode"],
        poc_file_path=poc_file_path,
    )

    detection_metrics["compile_ok"] = True
    detection_metrics["compile_attempts"] = len(compile_attempts)
    detection_metrics["compile_fallback_used"] = compile_precheck["used_fallback"]
    detection_metrics["compile_strategy"] = chosen_compile["label"]
    detection_metrics["compile_returncode"] = chosen_compile["returncode"]
    detection_metrics["compile_timeout"] = chosen_compile["timeout"]
    detection_metrics["test_returncode"] = test_result["returncode"]
    detection_metrics["test_timeout"] = test_result["timeout"]

    status = "VULNERABLE" if matched else "NOT_VULNERABLE"
    log_path = out_dir / "logs" / f"{target_id}.log"
    write_task_log(
        log_path,
        target_id=target_id,
        repo_path=repo_path,
        exec_dir=exec_dir,
        module=str(module),
        dtest=str(dtest),
        mode=mode,
        compile_attempts=compile_attempts,
        test_command=test_cmd,
        start_time=start_time,
        end_time=end_time,
        compile_returncode=chosen_compile["returncode"],
        compile_timeout=chosen_compile["timeout"],
        test_returncode=test_result["returncode"],
        test_timeout=test_result["timeout"],
        detection_info=detection_info,
        detection_metrics=detection_metrics,
        status=status,
        test_stdout=test_result["stdout"],
        test_stderr=test_result["stderr"],
        poc_file_path=poc_file_path,
        surefire_files=surefire_files,
        surefire_text=surefire_text,
    )

    return (status, target_id, detection_info, mode, detection_metrics)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Batch runner: validate vulnerable behavior on original repos described "
            "in YAML, with additional match-count statistics."
        )
    )
    parser.add_argument("--yaml", required=True, help="Path to tasks YAML")
    parser.add_argument(
        "--repo_root",
        required=True,
        help="Original repo root, expected layout: repo_root/<target_id>",
    )
    parser.add_argument("--out_dir", required=True, help="Directory to store logs and summary")
    parser.add_argument("--timeout", type=int, default=1800, help="Per-task timeout in seconds")
    parser.add_argument("--mvn", default="mvn", help="Maven binary to use")
    parser.add_argument(
        "--workers",
        type=int,
        choices=[1],
        default=1,
        help="Number of tasks to run concurrently (fixed at 1)",
    )
    parser.add_argument(
        "--target_id",
        action="append",
        dest="target_ids",
        help="Run only the given target_id; may be repeated",
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml).resolve()
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    logs_dir = out_dir / "logs"

    if not yaml_path.is_file():
        print(f"[ERROR] YAML not found: {yaml_path}")
        sys.exit(1)
    if not repo_root.is_dir():
        print(f"[ERROR] repo_root not found: {repo_root}")
        sys.exit(1)
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list) or not tasks:
        print("[ERROR] YAML must contain a non-empty list at key: tasks")
        sys.exit(1)

    if args.target_ids:
        selected = set(args.target_ids)
        tasks = [task for task in tasks if task.get("target_id") in selected]
        if not tasks:
            print(f"[ERROR] No tasks matched --target_id: {sorted(selected)}")
            sys.exit(1)

    logs_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "VULNERABLE": [],
        "NOT_VULNERABLE": [],
        "COMPILE_FAILED": [],
        "ERROR": [],
    }
    summary_counters = init_summary_counters()

    valid_tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            results["ERROR"].append(
                {"target_id": "UNKNOWN", "info": "task item is not a dict"}
            )
            continue

        valid_tasks.append(task)

    worker_count = 1
    print(f"[INFO] Running {len(valid_tasks)} task(s) sequentially")
    task_results = [
        run_one_task(
            mvn_bin=args.mvn,
            repo_root=repo_root,
            out_dir=out_dir,
            timeout_sec=args.timeout,
            task=task,
        )
        for task in valid_tasks
    ]

    for task, task_result in zip(valid_tasks, task_results):
        status, target_id, info, mode, metrics = task_result

        item = {"target_id": target_id, "info": info}
        if mode is not None:
            item["mode"] = mode
        if metrics is not None:
            item["metrics"] = metrics
            update_summary_counters(summary_counters, task, mode, metrics)
        elif mode is not None:
            summary_counters["detection_mode_counts"][mode] += 1
            for field in DETECTION_FIELDS:
                if task.get(field) is not None:
                    summary_counters["detection_field_counts"][field] += 1

        results[status].append(item)

    summary = {
        "yaml": str(yaml_path),
        "repo_root": str(repo_root),
        "out_dir": str(out_dir),
        "timeout": args.timeout,
        "workers": worker_count,
        "task_count": len(tasks),
        "counts": {k: len(v) for k, v in results.items()},
        "detection_mode_counts": summary_counters["detection_mode_counts"],
        "detection_field_counts": summary_counters["detection_field_counts"],
        "matched_content_total_counts": summary_counters["matched_content_total_counts"],
        "details": results,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary_csv(out_dir / "summary.csv", summary)

    print("\n" + "#" * 80)
    print("BATCH SUMMARY")
    print("#" * 80)

    print(f"\nTASK_COUNT: {len(tasks)}")
    print("\nDETECTION_MODE_COUNTS:")
    for key in DETECTION_MODES:
        print(f"  - {key}: {summary_counters['detection_mode_counts'][key]}")

    print("\nDETECTION_FIELD_COUNTS:")
    for key in DETECTION_FIELDS:
        print(f"  - {key}: {summary_counters['detection_field_counts'][key]}")

    print("\nMATCHED_CONTENT_TOTAL_COUNTS:")
    for key in DETECTION_MODES:
        print(f"  - {key}: {summary_counters['matched_content_total_counts'][key]}")

    for key in ["VULNERABLE", "NOT_VULNERABLE", "COMPILE_FAILED", "ERROR"]:
        print(f"\n{key}: {len(results[key])}")
        for item in results[key]:
            target_id = item.get("target_id")
            info = item.get("info")
            print(f"  - {target_id}: {info}")

    if results["ERROR"]:
        sys.exit(2)
    if results["NOT_VULNERABLE"] or results["COMPILE_FAILED"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
