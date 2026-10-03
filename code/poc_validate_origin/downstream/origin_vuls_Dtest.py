#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch runner for validating vulnerable behavior on original downstream repos.

Compared with patch_Dtest.py:
- reads the same YAML task format
- uses original repositories directly from repo_root / target_id
- runs the declared Dtest with Maven in repo_root / target_id / module
- determines vulnerable/not-vulnerable by the YAML detection fields

Supported detection modes (mutually exclusive):
- poc_file
- poc_exit
- poc_string2
- poc_cmd
- else default poc_string

Typical repo layout for this script:
- /path/to/resource/<target_id>
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


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


def evaluate_detection(
    mode: str,
    task: dict,
    combined_output: str,
    returncode: int,
    poc_file_path: Path | None,
) -> tuple[bool, str]:
    if mode == "poc_file":
        if poc_file_path is None:
            return False, "poc_file mode selected but path is missing"
        matched = poc_file_path.exists()
        return matched, f"poc_file exists={matched}: {poc_file_path}"

    if mode == "poc_exit":
        expected = int(task["poc_exit"])
        matched = returncode == expected
        return matched, f"returncode={returncode}, expected={expected}"

    if mode == "poc_string2":
        expected = str(task["poc_string2"])
        matched = expected.casefold() in combined_output.casefold()
        return matched, f"poc_string2 matched={matched} (case-insensitive): {expected!r}"

    if mode == "poc_cmd":
        expected = str(task["poc_cmd"])
        matched = expected.casefold() in combined_output.casefold()
        return matched, f"poc_cmd matched={matched} (case-insensitive): {expected!r}"

    expected = task.get("poc_string")
    if expected is None:
        return False, "poc_string mode selected but poc_string is missing"
    expected = str(expected)
    matched = expected.casefold() in combined_output.casefold()
    return matched, f"poc_string matched={matched} (case-insensitive): {expected!r}"


def write_task_log(
    log_path: Path,
    *,
    target_id: str,
    repo_path: Path,
    exec_dir: Path,
    module: str,
    dtest: str,
    mode: str,
    command: list[str],
    start_time: str,
    end_time: str,
    returncode: int,
    timeout: bool,
    detection_info: str,
    status: str,
    stdout: str,
    stderr: str,
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
        f"command: {' '.join(command)}",
        f"start_time: {start_time}",
        f"end_time: {end_time}",
        f"returncode: {returncode}",
        f"timeout: {timeout}",
        f"status: {status}",
        f"detection: {detection_info}",
    ]

    if poc_file_path is not None:
        lines.append(f"poc_file_path: {poc_file_path}")
    if surefire_files:
        lines.append("surefire_files:")
        lines.extend(surefire_files)

    lines.extend(
        [
            "",
            "===== STDOUT =====",
            stdout or "",
            "",
            "===== STDERR =====",
            stderr or "",
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


def run_one_task(
    mvn_bin: str,
    repo_root: Path,
    out_dir: Path,
    timeout_sec: int,
    task: dict,
):
    target_id = task.get("target_id")
    if not target_id:
        return ("ERROR", None, "missing target_id")

    module = task.get("module", ".")
    dtest = task.get("Dtest")
    if not dtest:
        return ("ERROR", target_id, "missing Dtest")

    try:
        mode = detect_mode(task)
    except Exception as exc:
        return ("ERROR", target_id, str(exc))

    repo_path = resolve_repo_path(repo_root, target_id)
    exec_dir = resolve_module_path(repo_path, module)

    if not repo_path.is_dir():
        return ("ERROR", target_id, f"repo not found: {repo_path}")
    if not exec_dir.is_dir():
        return ("ERROR", target_id, f"module dir not found: {exec_dir}")

    poc_file_path = resolve_poc_file_path(exec_dir, task.get("poc_file"))
    ok, cleanup_info = cleanup_poc_file(poc_file_path)
    if not ok:
        return ("ERROR", target_id, cleanup_info)

    cmd = [mvn_bin, "clean", "test", f"-Dtest={dtest}"]

    print("\n" + "=" * 80)
    print(f"[TASK] target_id={target_id}")
    print(f"[INFO] repo     = {repo_path}")
    print(f"[INFO] module   = {module}")
    print(f"[INFO] exec_dir = {exec_dir}")
    print(f"[INFO] Dtest    = {dtest}")
    print(f"[INFO] mode     = {mode}")
    if poc_file_path is not None:
        print(f"[INFO] poc_file = {poc_file_path}")
    if mode == "poc_cmd":
        print(f"[INFO] poc_cmd  = {task.get('poc_cmd')}")
    if mode == "poc_string":
        print(f"[INFO] poc_str  = {task.get('poc_string')}")
    print(f"[INFO] command  = {' '.join(cmd)}")
    print("=" * 80)

    start_time = datetime.now().isoformat(timespec="seconds")
    stdout = ""
    stderr = ""
    timeout = False
    returncode = -1

    try:
        completed = subprocess.run(
            cmd,
            cwd=exec_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (
            (exc.stderr or "")
            + f"\n[ERROR] timeout after {timeout_sec} seconds; command timed out"
        )
        timeout = True
        returncode = -1
    except Exception as exc:
        end_time = datetime.now().isoformat(timespec="seconds")
        log_path = out_dir / "logs" / f"{target_id}.log"
        write_task_log(
            log_path,
            target_id=target_id,
            repo_path=repo_path,
            exec_dir=exec_dir,
            module=str(module),
            dtest=str(dtest),
            mode=mode,
            command=cmd,
            start_time=start_time,
            end_time=end_time,
            returncode=-1,
            timeout=False,
            detection_info=f"execution error: {type(exc).__name__}: {exc}",
            status="ERROR",
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}",
            poc_file_path=poc_file_path,
            surefire_files=[],
            surefire_text="",
        )
        return ("ERROR", target_id, f"execution error: {type(exc).__name__}: {exc}")

    end_time = datetime.now().isoformat(timespec="seconds")
    surefire_text, surefire_files = collect_surefire_reports(exec_dir)
    combined_output = f"{stdout}\n{stderr}\n{surefire_text}"
    matched, detection_info = evaluate_detection(
        mode=mode,
        task=task,
        combined_output=combined_output,
        returncode=returncode,
        poc_file_path=poc_file_path,
    )

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
        command=cmd,
        start_time=start_time,
        end_time=end_time,
        returncode=returncode,
        timeout=timeout,
        detection_info=detection_info,
        status=status,
        stdout=stdout,
        stderr=stderr,
        poc_file_path=poc_file_path,
        surefire_files=surefire_files,
        surefire_text=surefire_text,
    )

    return (status, target_id, detection_info)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Batch runner: validate vulnerable behavior on original repos described in YAML."
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

    results = {"VULNERABLE": [], "NOT_VULNERABLE": [], "ERROR": []}

    for task in tasks:
        if not isinstance(task, dict):
            results["ERROR"].append(("UNKNOWN", "task item is not a dict"))
            continue

        status, target_id, info = run_one_task(
            mvn_bin=args.mvn,
            repo_root=repo_root,
            out_dir=out_dir,
            timeout_sec=args.timeout,
            task=task,
        )
        results[status].append((target_id, info))

    summary = {
        "yaml": str(yaml_path),
        "repo_root": str(repo_root),
        "out_dir": str(out_dir),
        "timeout": args.timeout,
        "counts": {k: len(v) for k, v in results.items()},
        "details": {
            k: [{"target_id": tid, "info": info} for tid, info in values]
            for k, values in results.items()
        },
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "#" * 80)
    print("BATCH SUMMARY")
    print("#" * 80)

    for key in ["VULNERABLE", "NOT_VULNERABLE", "ERROR"]:
        print(f"\n{key}: {len(results[key])}")
        for target_id, info in results[key]:
            print(f"  - {target_id}: {info}")

    if results["ERROR"]:
        sys.exit(2)
    if results["NOT_VULNERABLE"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
