#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch runner for validating vulnerable behavior after testing multiple patches.

Goal:
- keep the detection/statistics style of origin_vuls_Dtest_count.py
- for each target repo, test multiple patches one by one
- reset the repo back to a Git baseline before the next patch
- choose the patch with the smallest vulnerability-marker count as the final
  result for that target
- run all targets and their patches sequentially

Safety model:
- the original repo under repo_root is never modified
- each target is copied to a dedicated work directory
- the copied repo is initialized with `git init`, `git add -A`, `git commit`
- every patch is tested on that copied baseline and then rolled back

YAML task format:
- compatible with the existing origin_vuls_Dtest_count.py task fields
- extra optional fields for patch discovery:
  * patches: explicit patch list; each item may be absolute or relative to
    --patch_root
  * patch_dir: directory containing candidate patches; may be absolute or
    relative to --patch_root
  * patch_glob: glob used inside patch_dir, default "*.patch"

If patches/patch_dir are omitted, the script auto-discovers patches with:
1. <patch_root>/<target_id>/*.patch
2. <patch_root>/<target_id>.patch
"""

import argparse
import csv
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import yaml


DETECTION_FIELDS = ["poc_string", "poc_file", "poc_exit", "poc_string2", "poc_cmd"]
DETECTION_MODES = ["poc_string", "poc_file", "poc_exit", "poc_string2", "poc_cmd"]
PRIMARY_PRECHECK_ARGS = ["clean", "install", "-DskipTests"]
FALLBACK_PRECHECK_ARGS = ["clean", "install", "-Dmaven.test.skip=true"]
FINAL_STATUSES = ["VULNERABLE", "NOT_VULNERABLE", "COMPILE_FAILED", "ERROR"]
PATCH_APPLY_STRATEGIES = [
    ("standard", []),
    ("unidiff_zero", ["--unidiff-zero"]),
    (
        "unidiff_zero_ignore_whitespace",
        ["--unidiff-zero", "--ignore-space-change", "--ignore-whitespace"],
    ),
    (
        "unidiff_zero_whitespace_nowarn",
        ["--unidiff-zero", "--whitespace=nowarn"],
    ),
]
DEFAULT_MATCH_COUNT_SENTINEL = 10**12


def detect_mode(task: dict) -> str:
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


def sanitize_name(raw: str) -> str:
    cleaned = []
    for ch in raw:
        if ch.isalnum() or ch in ("-", "_", "."):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("._") or "item"


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


def resolve_patch_candidates(task: dict, patch_root: Path | None) -> list[Path]:
    explicit = task.get("patches")
    patch_dir_value = task.get("patch_dir")
    patch_glob = str(task.get("patch_glob") or "*.patch")
    target_id = str(task.get("target_id") or "")

    candidates: list[Path] = []

    if explicit is not None:
        if not isinstance(explicit, list) or not explicit:
            raise ValueError("patches must be a non-empty list when provided")
        for item in explicit:
            path = Path(str(item))
            if not path.is_absolute():
                if patch_root is None:
                    raise ValueError("relative patch path requires --patch_root")
                path = patch_root / path
            candidates.append(path.resolve())
        return dedupe_paths(candidates)

    if patch_dir_value is not None:
        patch_dir = Path(str(patch_dir_value))
        if not patch_dir.is_absolute():
            if patch_root is None:
                raise ValueError("relative patch_dir requires --patch_root")
            patch_dir = patch_root / patch_dir
        patch_dir = patch_dir.resolve()
        if not patch_dir.is_dir():
            raise ValueError(f"patch_dir not found: {patch_dir}")
        candidates.extend(sorted(path.resolve() for path in patch_dir.glob(patch_glob) if path.is_file()))
        return dedupe_paths(candidates)

    if patch_root is None:
        raise ValueError("no patches/patch_dir in task and --patch_root is missing")

    target_patch_dir = (patch_root / target_id).resolve()
    target_patch_file = (patch_root / f"{target_id}.patch").resolve()

    if target_patch_dir.is_dir():
        candidates.extend(sorted(path.resolve() for path in target_patch_dir.glob(patch_glob) if path.is_file()))
    if target_patch_file.is_file():
        candidates.append(target_patch_file)

    candidates = dedupe_paths(candidates)
    if not candidates:
        raise ValueError(
            "no patch candidates found; tried "
            f"{target_patch_dir}/{patch_glob} and {target_patch_file}"
        )
    return candidates


def dedupe_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    result = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def copy_repo_to_workdir(src_repo: Path, work_root: Path, target_id: str) -> Path:
    work_root.mkdir(parents=True, exist_ok=True)
    work_repo = (work_root / f"{sanitize_name(target_id)}_{uuid.uuid4().hex}").resolve()
    shutil.copytree(src_repo, work_repo, ignore=shutil.ignore_patterns(".git"))
    return work_repo


def ensure_git_baseline(git_bin: str, repo_path: Path, timeout_sec: int) -> tuple[bool, str, str, list[dict]]:
    commands = [
        [git_bin, "init"],
        [git_bin, "config", "user.name", "vuln-patch-tester"],
        [git_bin, "config", "user.email", "vuln-patch-tester@example.invalid"],
        [git_bin, "add", "-A"],
        [git_bin, "commit", "-m", "baseline"],
    ]

    attempts = []
    for cmd in commands:
        result = run_command(cmd, cwd=repo_path, timeout_sec=timeout_sec)
        attempts.append({"cmd": cmd, **result})
        if result["error"] is not None or result["returncode"] != 0:
            return False, "", f"git baseline setup failed: {' '.join(cmd)}", attempts

    head_result = run_command([git_bin, "rev-parse", "HEAD"], cwd=repo_path, timeout_sec=timeout_sec)
    attempts.append({"cmd": [git_bin, "rev-parse", "HEAD"], **head_result})
    if head_result["error"] is not None or head_result["returncode"] != 0:
        return False, "", "failed to resolve baseline commit", attempts

    baseline_commit = (head_result["stdout"] or "").strip()
    if not baseline_commit:
        return False, "", "baseline commit hash is empty", attempts
    return True, baseline_commit, "", attempts


def reset_to_baseline(git_bin: str, repo_path: Path, baseline_commit: str, timeout_sec: int) -> tuple[bool, str, list[dict]]:
    commands = [
        [git_bin, "reset", "--hard", baseline_commit],
        [git_bin, "clean", "-fd"],
    ]
    attempts = []
    for cmd in commands:
        result = run_command(cmd, cwd=repo_path, timeout_sec=timeout_sec)
        attempts.append({"cmd": cmd, **result})
        if result["error"] is not None or result["returncode"] != 0:
            return False, f"git reset failed: {' '.join(cmd)}", attempts
    return True, "", attempts


def apply_patch_with_git(
    git_bin: str,
    repo_path: Path,
    patch_path: Path,
    timeout_sec: int,
) -> tuple[bool, str, list[dict]]:
    attempts = []

    for label, extra_args in PATCH_APPLY_STRATEGIES:
        check_cmd = [git_bin, "apply", *extra_args, "--check", str(patch_path)]
        check_result = run_command(check_cmd, cwd=repo_path, timeout_sec=timeout_sec)
        attempts.append({"label": f"{label}_check", "cmd": check_cmd, **check_result})
        if check_result["error"] is not None:
            continue
        if check_result["returncode"] != 0:
            continue

        apply_cmd = [git_bin, "apply", *extra_args, str(patch_path)]
        apply_result = run_command(apply_cmd, cwd=repo_path, timeout_sec=timeout_sec)
        attempts.append({"label": f"{label}_apply", "cmd": apply_cmd, **apply_result})
        if apply_result["error"] is None and apply_result["returncode"] == 0:
            return True, f"patch applied with strategy={label}", attempts

    return False, "patch apply failed", attempts


def choose_best_patch_result(patch_results: list[dict]) -> dict:
    if not patch_results:
        raise ValueError("patch_results is empty")

    def rank(item: dict) -> tuple:
        metrics = item.get("metrics") or {}
        compile_ok = bool(metrics.get("compile_ok"))
        status = str(item.get("status"))
        match_count = (
            int(metrics.get("match_count", DEFAULT_MATCH_COUNT_SENTINEL))
            if compile_ok
            else DEFAULT_MATCH_COUNT_SENTINEL
        )
        status_rank = {
            "NOT_VULNERABLE": 0,
            "VULNERABLE": 1,
            "COMPILE_FAILED": 2,
            "ERROR": 3,
        }.get(status, 99)
        fallback_rank = 1 if metrics.get("compile_fallback_used") else 0
        return (
            0 if compile_ok else 1,
            match_count,
            status_rank,
            fallback_rank,
            int(item.get("patch_index", 0)),
            str(item.get("patch_label", "")),
        )

    return min(patch_results, key=rank)


def build_patch_result_item(
    *,
    status: str,
    target_id: str,
    mode: str,
    info: str,
    metrics: dict,
    patch_index: int,
    patch_path: Path,
    patch_label: str,
    log_path: Path,
) -> dict:
    item = {
        "status": status,
        "target_id": target_id,
        "mode": mode,
        "info": info,
        "metrics": metrics,
        "patch_index": patch_index,
        "patch_path": str(patch_path),
        "patch_label": patch_label,
        "log_path": str(log_path),
    }
    metrics_summary = item.get("metrics") or {}
    print(
        f"[PATCH-RESULT] target_id={target_id} patch={patch_index} "
        f"status={status} compile_ok={metrics_summary.get('compile_ok')} "
        f"match_count={metrics_summary.get('match_count')} "
        f"log={log_path}"
    )
    return item


def write_patch_log(
    log_path: Path,
    *,
    target_id: str,
    patch_index: int,
    patch_label: str,
    patch_path: Path,
    source_repo_path: Path,
    work_repo_path: Path,
    exec_dir: Path,
    module: str,
    dtest: str,
    mode: str,
    git_baseline_commit: str,
    git_setup_attempts: list[dict],
    reset_attempts_before: list[dict],
    reset_attempts_after: list[dict],
    patch_apply_attempts: list[dict],
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
        f"patch_index: {patch_index}",
        f"patch_label: {patch_label}",
        f"patch_path: {patch_path}",
        f"source_repo_path: {source_repo_path}",
        f"work_repo_path: {work_repo_path}",
        f"exec_dir: {exec_dir}",
        f"module: {module}",
        f"Dtest: {dtest}",
        f"mode: {mode}",
        f"git_baseline_commit: {git_baseline_commit}",
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

    if poc_file_path is not None:
        lines.append(f"poc_file_path: {poc_file_path}")
    if surefire_files:
        lines.append("surefire_files:")
        lines.extend(surefire_files)

    def append_attempts(title: str, attempts: list[dict]) -> None:
        lines.append("")
        lines.append(f"===== {title} =====")
        if not attempts:
            lines.append("(none)")
            return
        for idx, attempt in enumerate(attempts, start=1):
            label = attempt.get("label")
            lines.append(f"[{idx}] command: {' '.join(attempt.get('cmd', []))}")
            if label is not None:
                lines.append(f"[{idx}] label: {label}")
            lines.append(f"[{idx}] returncode: {attempt.get('returncode')}")
            lines.append(f"[{idx}] timeout: {attempt.get('timeout')}")
            lines.append(f"[{idx}] error: {attempt.get('error')}")
            lines.append("")
            lines.append(f"[{idx}] STDOUT")
            lines.append(attempt.get("stdout") or "")
            lines.append("")
            lines.append(f"[{idx}] STDERR")
            lines.append(attempt.get("stderr") or "")
            lines.append("")

    append_attempts("GIT SETUP", git_setup_attempts)
    append_attempts("RESET BEFORE PATCH", reset_attempts_before)
    append_attempts("PATCH APPLY", patch_apply_attempts)
    append_attempts("COMPILE PRECHECK", compile_attempts)

    lines.extend(
        [
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

    append_attempts("RESET AFTER PATCH", reset_attempts_after)
    log_path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_csv(csv_path: Path, summary: dict) -> None:
    fieldnames = [
        "status",
        "target_id",
        "mode",
        "best_patch_label",
        "best_patch_path",
        "patch_candidates",
        "successful_patch_count",
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

        for status in FINAL_STATUSES:
            for item in summary["details"].get(status, []):
                metrics = item.get("metrics", {}) or {}
                writer.writerow(
                    {
                        "status": status,
                        "target_id": item.get("target_id"),
                        "mode": item.get("mode"),
                        "best_patch_label": item.get("best_patch_label"),
                        "best_patch_path": item.get("best_patch_path"),
                        "patch_candidates": item.get("patch_candidates"),
                        "successful_patch_count": item.get("successful_patch_count"),
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


def run_one_patch(
    *,
    mvn_bin: str,
    git_bin: str,
    timeout_sec: int,
    task: dict,
    target_id: str,
    mode: str,
    module: str,
    dtest: str,
    source_repo_path: Path,
    work_repo_path: Path,
    exec_dir: Path,
    baseline_commit: str,
    git_setup_attempts: list[dict],
    patch_index: int,
    patch_total: int,
    patch_path: Path,
    log_dir: Path,
) -> dict:
    patch_label = patch_path.stem
    log_name = f"{sanitize_name(target_id)}__{patch_index:03d}__{sanitize_name(patch_label)}.log"
    log_path = log_dir / log_name

    print(f"[PATCH] target_id={target_id} patch={patch_index}/{patch_total}")
    print(f"[PATCH] patch_label={patch_label}")
    print(f"[PATCH] patch_path={patch_path}")

    reset_attempts_before: list[dict] = []
    reset_attempts_after: list[dict] = []
    patch_apply_attempts: list[dict] = []
    compile_attempts: list[dict] = []
    surefire_files: list[str] = []
    surefire_text = ""
    test_stdout = ""
    test_stderr = ""
    detection_info = ""
    compile_returncode = -1
    compile_timeout = False
    test_returncode = -1
    test_timeout = False
    status = "ERROR"
    start_time = datetime.now().isoformat(timespec="seconds")

    poc_file_path = resolve_poc_file_path(exec_dir, task.get("poc_file"))
    test_cmd = [mvn_bin, "clean", "test", f"-Dtest={dtest}"]

    try:
        ok, reset_info, reset_attempts_before = reset_to_baseline(
            git_bin,
            work_repo_path,
            baseline_commit,
            timeout_sec,
        )
        if not ok:
            detection_metrics = {
                "mode": mode,
                "match_count": 0,
                "compile_ok": False,
                "compile_attempts": 0,
                "compile_fallback_used": False,
                "compile_strategy": None,
                "compile_returncode": -1,
                "compile_timeout": False,
                "test_returncode": -1,
                "test_timeout": False,
            }
            detection_info = reset_info
            end_time = datetime.now().isoformat(timespec="seconds")
            write_patch_log(
                log_path,
                target_id=target_id,
                patch_index=patch_index,
                patch_label=patch_label,
                patch_path=patch_path,
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                module=str(module),
                dtest=str(dtest),
                mode=mode,
                git_baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                reset_attempts_before=reset_attempts_before,
                reset_attempts_after=reset_attempts_after,
                patch_apply_attempts=patch_apply_attempts,
                compile_attempts=compile_attempts,
                test_command=test_cmd,
                start_time=start_time,
                end_time=end_time,
                compile_returncode=compile_returncode,
                compile_timeout=compile_timeout,
                test_returncode=test_returncode,
                test_timeout=test_timeout,
                detection_info=detection_info,
                detection_metrics=detection_metrics,
                status=status,
                test_stdout=test_stdout,
                test_stderr=test_stderr,
                poc_file_path=poc_file_path,
                surefire_files=surefire_files,
                surefire_text=surefire_text,
            )
            return build_patch_result_item(
                status=status,
                target_id=target_id,
                mode=mode,
                info=detection_info,
                metrics=detection_metrics,
                patch_index=patch_index,
                patch_path=patch_path,
                patch_label=patch_label,
                log_path=log_path,
            )

        ok, cleanup_info = cleanup_poc_file(poc_file_path)
        if not ok:
            detection_metrics = {
                "mode": mode,
                "match_count": 0,
                "compile_ok": False,
                "compile_attempts": 0,
                "compile_fallback_used": False,
                "compile_strategy": None,
                "compile_returncode": -1,
                "compile_timeout": False,
                "test_returncode": -1,
                "test_timeout": False,
            }
            detection_info = cleanup_info
            end_time = datetime.now().isoformat(timespec="seconds")
            write_patch_log(
                log_path,
                target_id=target_id,
                patch_index=patch_index,
                patch_label=patch_label,
                patch_path=patch_path,
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                module=str(module),
                dtest=str(dtest),
                mode=mode,
                git_baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                reset_attempts_before=reset_attempts_before,
                reset_attempts_after=reset_attempts_after,
                patch_apply_attempts=patch_apply_attempts,
                compile_attempts=compile_attempts,
                test_command=test_cmd,
                start_time=start_time,
                end_time=end_time,
                compile_returncode=compile_returncode,
                compile_timeout=compile_timeout,
                test_returncode=test_returncode,
                test_timeout=test_timeout,
                detection_info=detection_info,
                detection_metrics=detection_metrics,
                status=status,
                test_stdout=test_stdout,
                test_stderr=test_stderr,
                poc_file_path=poc_file_path,
                surefire_files=surefire_files,
                surefire_text=surefire_text,
            )
            return build_patch_result_item(
                status=status,
                target_id=target_id,
                mode=mode,
                info=detection_info,
                metrics=detection_metrics,
                patch_index=patch_index,
                patch_path=patch_path,
                patch_label=patch_label,
                log_path=log_path,
            )

        patch_applied, apply_info, patch_apply_attempts = apply_patch_with_git(
            git_bin,
            work_repo_path,
            patch_path,
            timeout_sec,
        )
        if not patch_applied:
            detection_metrics = {
                "mode": mode,
                "match_count": 0,
                "compile_ok": False,
                "compile_attempts": 0,
                "compile_fallback_used": False,
                "compile_strategy": None,
                "compile_returncode": -1,
                "compile_timeout": False,
                "test_returncode": -1,
                "test_timeout": False,
            }
            detection_info = apply_info
            end_time = datetime.now().isoformat(timespec="seconds")
            write_patch_log(
                log_path,
                target_id=target_id,
                patch_index=patch_index,
                patch_label=patch_label,
                patch_path=patch_path,
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                module=str(module),
                dtest=str(dtest),
                mode=mode,
                git_baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                reset_attempts_before=reset_attempts_before,
                reset_attempts_after=reset_attempts_after,
                patch_apply_attempts=patch_apply_attempts,
                compile_attempts=compile_attempts,
                test_command=test_cmd,
                start_time=start_time,
                end_time=end_time,
                compile_returncode=compile_returncode,
                compile_timeout=compile_timeout,
                test_returncode=test_returncode,
                test_timeout=test_timeout,
                detection_info=detection_info,
                detection_metrics=detection_metrics,
                status=status,
                test_stdout=test_stdout,
                test_stderr=test_stderr,
                poc_file_path=poc_file_path,
                surefire_files=surefire_files,
                surefire_text=surefire_text,
            )
            return build_patch_result_item(
                status=status,
                target_id=target_id,
                mode=mode,
                info=detection_info,
                metrics=detection_metrics,
                patch_index=patch_index,
                patch_path=patch_path,
                patch_label=patch_label,
                log_path=log_path,
            )

        compile_precheck = run_compile_precheck(mvn_bin, cwd=exec_dir, timeout_sec=timeout_sec)
        compile_attempts = compile_precheck["attempts"]
        chosen_compile = compile_precheck["chosen_attempt"]
        compile_returncode = chosen_compile["returncode"]
        compile_timeout = chosen_compile["timeout"]

        if chosen_compile["error"] is not None and not compile_precheck["success"]:
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
            end_time = datetime.now().isoformat(timespec="seconds")
            write_patch_log(
                log_path,
                target_id=target_id,
                patch_index=patch_index,
                patch_label=patch_label,
                patch_path=patch_path,
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                module=str(module),
                dtest=str(dtest),
                mode=mode,
                git_baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                reset_attempts_before=reset_attempts_before,
                reset_attempts_after=reset_attempts_after,
                patch_apply_attempts=patch_apply_attempts,
                compile_attempts=compile_attempts,
                test_command=test_cmd,
                start_time=start_time,
                end_time=end_time,
                compile_returncode=-1,
                compile_timeout=False,
                test_returncode=test_returncode,
                test_timeout=test_timeout,
                detection_info=detection_info,
                detection_metrics=detection_metrics,
                status=status,
                test_stdout=test_stdout,
                test_stderr=test_stderr,
                poc_file_path=poc_file_path,
                surefire_files=surefire_files,
                surefire_text=surefire_text,
            )
            return build_patch_result_item(
                status=status,
                target_id=target_id,
                mode=mode,
                info=detection_info,
                metrics=detection_metrics,
                patch_index=patch_index,
                patch_path=patch_path,
                patch_label=patch_label,
                log_path=log_path,
            )

        if not compile_precheck["success"]:
            status = "COMPILE_FAILED"
            primary_attempt = compile_attempts[0]
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
            detection_info = (
                "compile failed after fallback: "
                f"primary_returncode={primary_attempt['returncode']}, "
                f"primary_timeout={primary_attempt['timeout']}, "
                f"fallback_returncode={chosen_compile['returncode']}, "
                f"fallback_timeout={chosen_compile['timeout']}"
            )
            end_time = datetime.now().isoformat(timespec="seconds")
            write_patch_log(
                log_path,
                target_id=target_id,
                patch_index=patch_index,
                patch_label=patch_label,
                patch_path=patch_path,
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                module=str(module),
                dtest=str(dtest),
                mode=mode,
                git_baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                reset_attempts_before=reset_attempts_before,
                reset_attempts_after=reset_attempts_after,
                patch_apply_attempts=patch_apply_attempts,
                compile_attempts=compile_attempts,
                test_command=test_cmd,
                start_time=start_time,
                end_time=end_time,
                compile_returncode=compile_returncode,
                compile_timeout=compile_timeout,
                test_returncode=test_returncode,
                test_timeout=test_timeout,
                detection_info=detection_info,
                detection_metrics=detection_metrics,
                status=status,
                test_stdout=test_stdout,
                test_stderr=test_stderr,
                poc_file_path=poc_file_path,
                surefire_files=surefire_files,
                surefire_text=surefire_text,
            )
            return build_patch_result_item(
                status=status,
                target_id=target_id,
                mode=mode,
                info=detection_info,
                metrics=detection_metrics,
                patch_index=patch_index,
                patch_path=patch_path,
                patch_label=patch_label,
                log_path=log_path,
            )

        test_result = run_command(test_cmd, cwd=exec_dir, timeout_sec=timeout_sec)
        test_stdout = test_result["stdout"]
        test_stderr = test_result["stderr"]
        test_returncode = test_result["returncode"]
        test_timeout = test_result["timeout"]

        if test_result["error"] is not None:
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
            end_time = datetime.now().isoformat(timespec="seconds")
            write_patch_log(
                log_path,
                target_id=target_id,
                patch_index=patch_index,
                patch_label=patch_label,
                patch_path=patch_path,
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                module=str(module),
                dtest=str(dtest),
                mode=mode,
                git_baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                reset_attempts_before=reset_attempts_before,
                reset_attempts_after=reset_attempts_after,
                patch_apply_attempts=patch_apply_attempts,
                compile_attempts=compile_attempts,
                test_command=test_cmd,
                start_time=start_time,
                end_time=end_time,
                compile_returncode=compile_returncode,
                compile_timeout=compile_timeout,
                test_returncode=-1,
                test_timeout=False,
                detection_info=detection_info,
                detection_metrics=detection_metrics,
                status=status,
                test_stdout=test_stdout,
                test_stderr=test_result["error"],
                poc_file_path=poc_file_path,
                surefire_files=surefire_files,
                surefire_text=surefire_text,
            )
            return build_patch_result_item(
                status=status,
                target_id=target_id,
                mode=mode,
                info=detection_info,
                metrics=detection_metrics,
                patch_index=patch_index,
                patch_path=patch_path,
                patch_label=patch_label,
                log_path=log_path,
            )

        surefire_text, surefire_files = collect_surefire_reports(exec_dir)
        combined_output = f"{test_stdout}\n{test_stderr}\n{surefire_text}"
        matched, detection_info, detection_metrics = evaluate_detection(
            mode=mode,
            task=task,
            combined_output=combined_output,
            returncode=test_returncode,
            poc_file_path=poc_file_path,
        )

        detection_metrics["compile_ok"] = True
        detection_metrics["compile_attempts"] = len(compile_attempts)
        detection_metrics["compile_fallback_used"] = compile_precheck["used_fallback"]
        detection_metrics["compile_strategy"] = chosen_compile["label"]
        detection_metrics["compile_returncode"] = chosen_compile["returncode"]
        detection_metrics["compile_timeout"] = chosen_compile["timeout"]
        detection_metrics["test_returncode"] = test_returncode
        detection_metrics["test_timeout"] = test_timeout
        status = "VULNERABLE" if matched else "NOT_VULNERABLE"

        end_time = datetime.now().isoformat(timespec="seconds")
        write_patch_log(
            log_path,
            target_id=target_id,
            patch_index=patch_index,
            patch_label=patch_label,
            patch_path=patch_path,
            source_repo_path=source_repo_path,
            work_repo_path=work_repo_path,
            exec_dir=exec_dir,
            module=str(module),
            dtest=str(dtest),
            mode=mode,
            git_baseline_commit=baseline_commit,
            git_setup_attempts=git_setup_attempts,
            reset_attempts_before=reset_attempts_before,
            reset_attempts_after=reset_attempts_after,
            patch_apply_attempts=patch_apply_attempts,
            compile_attempts=compile_attempts,
            test_command=test_cmd,
            start_time=start_time,
            end_time=end_time,
            compile_returncode=compile_returncode,
            compile_timeout=compile_timeout,
            test_returncode=test_returncode,
            test_timeout=test_timeout,
            detection_info=detection_info,
            detection_metrics=detection_metrics,
            status=status,
            test_stdout=test_stdout,
            test_stderr=test_stderr,
            poc_file_path=poc_file_path,
            surefire_files=surefire_files,
            surefire_text=surefire_text,
        )
        return build_patch_result_item(
            status=status,
            target_id=target_id,
            mode=mode,
            info=detection_info,
            metrics=detection_metrics,
            patch_index=patch_index,
            patch_path=patch_path,
            patch_label=patch_label,
            log_path=log_path,
        )
    finally:
        reset_ok, _, reset_attempts_after = reset_to_baseline(
            git_bin,
            work_repo_path,
            baseline_commit,
            timeout_sec,
        )
        if log_path.exists():
            with log_path.open("a", encoding="utf-8") as f:
                f.write("\n\n===== RESET AFTER PATCH (LATE APPEND) =====\n")
                for idx, attempt in enumerate(reset_attempts_after, start=1):
                    f.write(f"[{idx}] command: {' '.join(attempt.get('cmd', []))}\n")
                    f.write(f"[{idx}] returncode: {attempt.get('returncode')}\n")
                    f.write(f"[{idx}] timeout: {attempt.get('timeout')}\n")
                    f.write(f"[{idx}] error: {attempt.get('error')}\n")
                    f.write(f"[{idx}] STDOUT\n{attempt.get('stdout') or ''}\n")
                    f.write(f"[{idx}] STDERR\n{attempt.get('stderr') or ''}\n")
            if not reset_ok:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write("[ERROR] reset after patch failed\n")


def run_one_task(
    *,
    mvn_bin: str,
    git_bin: str,
    repo_root: Path,
    patch_root: Path | None,
    work_root: Path,
    out_dir: Path,
    timeout_sec: int,
    keep_workdirs: bool,
    task: dict,
) -> tuple[str, dict]:
    target_id = task.get("target_id")
    if not target_id:
        detail = {
            "target_id": None,
            "info": "missing target_id",
            "mode": None,
            "metrics": None,
            "best_patch_label": None,
            "best_patch_path": None,
            "patch_candidates": 0,
            "successful_patch_count": 0,
            "patch_results": [],
        }
        return "ERROR", detail

    module = task.get("module", ".")
    dtest = task.get("Dtest")
    if not dtest:
        detail = {
            "target_id": target_id,
            "info": "missing Dtest",
            "mode": None,
            "metrics": None,
            "best_patch_label": None,
            "best_patch_path": None,
            "patch_candidates": 0,
            "successful_patch_count": 0,
            "patch_results": [],
        }
        return "ERROR", detail

    try:
        mode = detect_mode(task)
    except Exception as exc:
        detail = {
            "target_id": target_id,
            "info": str(exc),
            "mode": None,
            "metrics": None,
            "best_patch_label": None,
            "best_patch_path": None,
            "patch_candidates": 0,
            "successful_patch_count": 0,
            "patch_results": [],
        }
        return "ERROR", detail

    source_repo_path = resolve_repo_path(repo_root, target_id)
    if not source_repo_path.is_dir():
        detail = {
            "target_id": target_id,
            "info": f"repo not found: {source_repo_path}",
            "mode": mode,
            "metrics": None,
            "best_patch_label": None,
            "best_patch_path": None,
            "patch_candidates": 0,
            "successful_patch_count": 0,
            "patch_results": [],
        }
        return "ERROR", detail

    try:
        patch_candidates = resolve_patch_candidates(task, patch_root)
    except Exception as exc:
        detail = {
            "target_id": target_id,
            "info": str(exc),
            "mode": mode,
            "metrics": None,
            "best_patch_label": None,
            "best_patch_path": None,
            "patch_candidates": 0,
            "successful_patch_count": 0,
            "patch_results": [],
        }
        return "ERROR", detail

    missing_patch = next((path for path in patch_candidates if not path.is_file()), None)
    if missing_patch is not None:
        detail = {
            "target_id": target_id,
            "info": f"patch not found: {missing_patch}",
            "mode": mode,
            "metrics": None,
            "best_patch_label": None,
            "best_patch_path": None,
            "patch_candidates": len(patch_candidates),
            "successful_patch_count": 0,
            "patch_results": [],
        }
        return "ERROR", detail

    print("\n" + "=" * 80)
    print(f"[TASK] target_id={target_id}")
    print(f"[INFO] source_repo = {source_repo_path}")
    print(f"[INFO] module      = {module}")
    print(f"[INFO] Dtest       = {dtest}")
    print(f"[INFO] mode        = {mode}")
    print(f"[INFO] patch_count = {len(patch_candidates)}")
    print("=" * 80)

    work_repo_path = copy_repo_to_workdir(source_repo_path, work_root, target_id)
    try:
        ok, baseline_commit, baseline_info, git_setup_attempts = ensure_git_baseline(
            git_bin,
            work_repo_path,
            timeout_sec,
        )
        if not ok:
            detail = {
                "target_id": target_id,
                "info": baseline_info,
                "mode": mode,
                "metrics": {
                    "mode": mode,
                    "match_count": 0,
                    "compile_ok": False,
                    "compile_attempts": 0,
                    "compile_fallback_used": False,
                    "compile_strategy": None,
                    "compile_returncode": -1,
                    "compile_timeout": False,
                    "test_returncode": -1,
                    "test_timeout": False,
                },
                "best_patch_label": None,
                "best_patch_path": None,
                "patch_candidates": len(patch_candidates),
                "successful_patch_count": 0,
                "patch_results": [],
                "git_setup_attempts": git_setup_attempts,
            }
            return "ERROR", detail

        exec_dir = resolve_module_path(work_repo_path, module)
        if not exec_dir.is_dir():
            detail = {
                "target_id": target_id,
                "info": f"module dir not found in work repo: {exec_dir}",
                "mode": mode,
                "metrics": {
                    "mode": mode,
                    "match_count": 0,
                    "compile_ok": False,
                    "compile_attempts": 0,
                    "compile_fallback_used": False,
                    "compile_strategy": None,
                    "compile_returncode": -1,
                    "compile_timeout": False,
                    "test_returncode": -1,
                    "test_timeout": False,
                },
                "best_patch_label": None,
                "best_patch_path": None,
                "patch_candidates": len(patch_candidates),
                "successful_patch_count": 0,
                "patch_results": [],
            }
            return "ERROR", detail

        log_dir = out_dir / "logs"
        patch_results = []
        for patch_index, patch_path in enumerate(patch_candidates, start=1):
            patch_result = run_one_patch(
                mvn_bin=mvn_bin,
                git_bin=git_bin,
                timeout_sec=timeout_sec,
                task=task,
                target_id=str(target_id),
                mode=mode,
                module=str(module),
                dtest=str(dtest),
                source_repo_path=source_repo_path,
                work_repo_path=work_repo_path,
                exec_dir=exec_dir,
                baseline_commit=baseline_commit,
                git_setup_attempts=git_setup_attempts,
                patch_index=patch_index,
                patch_total=len(patch_candidates),
                patch_path=patch_path,
                log_dir=log_dir,
            )
            patch_results.append(patch_result)

        best_patch = choose_best_patch_result(patch_results)
        successful_patch_count = sum(
            1 for item in patch_results if bool((item.get("metrics") or {}).get("compile_ok"))
        )
        detail = {
            "target_id": target_id,
            "info": best_patch["info"],
            "mode": mode,
            "metrics": best_patch["metrics"],
            "best_patch_label": best_patch["patch_label"],
            "best_patch_path": best_patch["patch_path"],
            "best_patch_log": best_patch["log_path"],
            "best_patch_index": best_patch["patch_index"],
            "patch_candidates": len(patch_candidates),
            "successful_patch_count": successful_patch_count,
            "patch_results": patch_results,
        }
        return best_patch["status"], detail
    finally:
        if not keep_workdirs:
            shutil.rmtree(work_repo_path, ignore_errors=True)


def sort_detail_lists(summary: dict) -> None:
    for status in FINAL_STATUSES:
        summary["details"][status].sort(key=lambda item: (str(item.get("target_id")), str(item.get("best_patch_label"))))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate vulnerable behavior on original repos after trying multiple "
            "candidate patches, then keep the best patch result per target."
        )
    )
    parser.add_argument("--yaml", required=True, help="Path to tasks YAML")
    parser.add_argument(
        "--repo_root",
        required=True,
        help="Original repo root, expected layout: repo_root/<target_id>",
    )
    parser.add_argument(
        "--patch_root",
        default=None,
        help=(
            "Patch root used by task-relative patch paths or auto-discovery. "
            "Auto-discovery tries patch_root/<target_id>/*.patch and patch_root/<target_id>.patch"
        ),
    )
    parser.add_argument("--out_dir", required=True, help="Directory to store logs and summary")
    parser.add_argument(
        "--work_root",
        default="/tmp/origin_vuls_multi_patch_workdirs",
        help="Temporary work root used for per-target repo copies",
    )
    parser.add_argument("--timeout", type=int, default=1800, help="Per-command timeout in seconds")
    parser.add_argument(
        "--jobs",
        type=int,
        choices=[1],
        default=1,
        help="How many targets to run in parallel (fixed at 1)",
    )
    parser.add_argument("--mvn", default="mvn", help="Maven executable")
    parser.add_argument("--git", default="git", help="Git executable")
    parser.add_argument(
        "--keep_workdirs",
        action="store_true",
        help="Keep copied work repos after execution for debugging",
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml).resolve()
    repo_root = Path(args.repo_root).resolve()
    patch_root = Path(args.patch_root).resolve() if args.patch_root else None
    out_dir = Path(args.out_dir).resolve()
    work_root = Path(args.work_root).resolve()

    if not yaml_path.is_file():
        print(f"[ERROR] YAML not found: {yaml_path}")
        sys.exit(1)
    if not repo_root.is_dir():
        print(f"[ERROR] repo_root not found: {repo_root}")
        sys.exit(1)
    if patch_root is not None and not patch_root.exists():
        print(f"[ERROR] patch_root not found: {patch_root}")
        sys.exit(1)

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list) or not tasks:
        print("[ERROR] YAML must contain a non-empty list at key: tasks")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "logs").mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)

    summary_counters = init_summary_counters()
    summary = {
        "yaml": str(yaml_path),
        "repo_root": str(repo_root),
        "patch_root": str(patch_root) if patch_root is not None else None,
        "out_dir": str(out_dir),
        "work_root": str(work_root),
        "timeout": args.timeout,
        "jobs": args.jobs,
        "task_count": len(tasks),
        "counts": {key: 0 for key in FINAL_STATUSES},
        "detection_mode_counts": summary_counters["detection_mode_counts"],
        "detection_field_counts": summary_counters["detection_field_counts"],
        "matched_content_total_counts": summary_counters["matched_content_total_counts"],
        "details": {key: [] for key in FINAL_STATUSES},
    }

    print(f"[INFO] Running {len(tasks)} task(s) sequentially")
    for task in tasks:
        if not isinstance(task, dict):
            item = {
                "target_id": "UNKNOWN",
                "info": "task item is not a dict",
                "mode": None,
                "metrics": None,
                "best_patch_label": None,
                "best_patch_path": None,
                "patch_candidates": 0,
                "successful_patch_count": 0,
                "patch_results": [],
            }
            summary["counts"]["ERROR"] += 1
            summary["details"]["ERROR"].append(item)
            continue

        try:
            status, detail = run_one_task(
                mvn_bin=args.mvn,
                git_bin=args.git,
                repo_root=repo_root,
                patch_root=patch_root,
                work_root=work_root,
                out_dir=out_dir,
                timeout_sec=args.timeout,
                keep_workdirs=args.keep_workdirs,
                task=task,
            )
        except Exception as exc:
            status = "ERROR"
            detail = {
                "target_id": task.get("target_id"),
                "info": f"unexpected exception: {type(exc).__name__}: {exc}",
                "mode": None,
                "metrics": None,
                "best_patch_label": None,
                "best_patch_path": None,
                "patch_candidates": 0,
                "successful_patch_count": 0,
                "patch_results": [],
            }

        summary["counts"][status] += 1
        summary["details"][status].append(detail)
        if detail.get("metrics") and detail.get("mode"):
            update_summary_counters(
                summary_counters,
                task,
                detail["mode"],
                detail["metrics"],
            )

    sort_detail_lists(summary)

    summary_json_path = out_dir / "summary.json"
    summary_csv_path = out_dir / "summary.csv"
    summary_json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary_csv(summary_csv_path, summary)

    print("\n" + "#" * 80)
    print("BEST PATCH SUMMARY")
    print("#" * 80)
    print(json.dumps(summary["counts"], ensure_ascii=False, indent=2))
    print(f"[INFO] summary.json = {summary_json_path}")
    print(f"[INFO] summary.csv  = {summary_csv_path}")


if __name__ == "__main__":
    main()
