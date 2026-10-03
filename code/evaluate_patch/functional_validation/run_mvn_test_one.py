#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# ANSI color codes
RESET = "\033[0m"
ORANGE = "\033[38;5;208m"
GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"


@dataclass
class TestStats:
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total: int = 0

    def to_dict(self):
        return {
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "total": self.total,
        }


def enable_ansi_on_windows() -> None:
    """
    Best-effort ANSI enabling for Windows terminals.
    On many CI environments / modern Windows terminals it already works.
    """
    if os.name == "nt":
        try:
            os.system("")
        except Exception:
            pass


def run(cmd: List[str], cwd: Optional[str] = None, check: bool = False) -> subprocess.CompletedProcess:
    """Run a command and capture combined stdout/stderr."""
    p = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p


def is_git_url(repo: str) -> bool:
    return repo.startswith(("http://", "https://", "git@", "ssh://")) or repo.endswith(".git")


def prepare_tmp_repo(repo: str, repo_copy: str) -> None:
    """Copy local repo or clone remote repo into repo_copy."""
    dst = Path(repo_copy)
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    dst.parent.mkdir(parents=True, exist_ok=True)

    src = Path(repo)
    if src.exists() and src.is_dir():
        shutil.copytree(src, dst)
    else:
        if not is_git_url(repo):
            raise RuntimeError(f"--repo is neither a directory nor a git url: {repo}")
        run(["git", "clone", "--depth", "1", repo, repo_copy], check=True)


def git_init(repo_copy: str) -> None:
    """Initialize git repository in tmp repo."""
    run(["git", "init"], cwd=repo_copy, check=True)
    # Not strictly required, but helps some workflows/tools
    run(["git", "add", "-A"], cwd=repo_copy, check=False)


def mvn_clean_test(repo_copy: str) -> subprocess.CompletedProcess:
    """Run mvn clean test."""
    return run(["mvn", "clean", "test"], cwd=repo_copy, check=False)


def find_surefire_xml_reports(repo_copy: str) -> List[Path]:
    """Recursively find surefire XML reports (multi-module supported)."""
    root = Path(repo_copy)

    reports = list(root.rglob("target/surefire-reports/TEST-*.xml"))
    reports += [p for p in root.rglob("target/surefire-reports/*.xml") if p.suffix.lower() == ".xml"]

    uniq = []
    seen = set()
    for p in reports:
        if p.is_file() and p not in seen:
            seen.add(p)
            uniq.append(p)

    return uniq


def parse_surefire_xml(path: Path) -> Tuple[int, int, int, int, int]:
    """
    Parse a surefire XML report and return:
    (tests, failures, errors, skipped, passed)
    """
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return (0, 0, 0, 0, 0)

    def read_suite(elem):
        tests = int(elem.attrib.get("tests", "0") or "0")
        failures = int(elem.attrib.get("failures", "0") or "0")
        errors = int(elem.attrib.get("errors", "0") or "0")
        skipped = int(elem.attrib.get("skipped", "0") or "0")
        return tests, failures, errors, skipped

    total_tests = total_failures = total_errors = total_skipped = 0

    if root.tag.endswith("testsuite"):
        t, f, e, s = read_suite(root)
        total_tests += t
        total_failures += f
        total_errors += e
        total_skipped += s
    else:
        for suite in root.findall(".//testsuite"):
            t, f, e, s = read_suite(suite)
            total_tests += t
            total_failures += f
            total_errors += e
            total_skipped += s

    passed = max(total_tests - total_failures - total_errors - total_skipped, 0)
    return total_tests, total_failures, total_errors, total_skipped, passed


def collect_test_stats(repo_copy: str) -> TestStats:
    """Aggregate all surefire XML reports into a single stats object."""
    stats = TestStats()
    reports = find_surefire_xml_reports(repo_copy)

    for rp in reports:
        t, f, e, s, p = parse_surefire_xml(rp)
        stats.total += t
        stats.failed += f
        stats.errors += e
        stats.skipped += s
        stats.passed += p

    return stats


def is_test_path(path: str) -> bool:
    """
    Detect whether a patch path belongs to test code.
    Common Maven/Java conventions:
      - src/test/
      - /test/ folders
      - *Test.java / *Tests.java / *IT.java
    """
    p = path.replace("\\", "/")

    if "/src/test/" in p or p.startswith("src/test/"):
        return True

    if "/test/" in p or p.startswith("test/"):
        return True

    base = os.path.basename(p)
    if re.search(r"(Test|Tests|IT)\.java$", base):
        return True

    return False


def strip_test_file_diffs(patch_text: str) -> str:
    """
    Remove diff blocks that modify test files.
    A block begins with: 'diff --git a/... b/...'
    """
    lines = patch_text.splitlines(keepends=True)
    out: List[str] = []

    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*?) b/(.*?)\s*$", line.strip())
            a_path = b_path = ""
            if m:
                a_path, b_path = m.group(1), m.group(2)

            block = [line]
            i += 1
            while i < n and not lines[i].startswith("diff --git "):
                block.append(lines[i])
                i += 1

            candidate = b_path or a_path
            if candidate and is_test_path(candidate):
                # Drop entire diff block for test paths
                continue

            out.extend(block)
        else:
            # Keep patch headers (e.g., From/Subject) or other non-diff lines
            out.append(line)
            i += 1

    return "".join(out)


def make_filtered_patch(original_patch_path: str) -> Optional[str]:
    """
    Create filtered patch file under /tmp/patch/<basename>,
    removing modifications for test files.
    Return path to filtered patch, or None if no non-test changes remain.
    """
    src = Path(original_patch_path)
    if not src.is_file():
        raise RuntimeError(f"Patch file not found: {original_patch_path}")

    patch_text = src.read_text(errors="replace")
    filtered = strip_test_file_diffs(patch_text)

    # If no diff blocks remain, skip applying
    if "diff --git " not in filtered:
        return None

    out_dir = Path("/tmp/patch")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / src.name
    out_path.write_text(filtered)
    return str(out_path)


def git_apply_patch(repo_copy: str, patch_path: str) -> subprocess.CompletedProcess:
    """Apply patch using git apply with whitespace-tolerant options."""
    return run(
        [
            "git",
            "apply",
            "--verbose",
            "--ignore-whitespace",
            "--ignore-space-change",
            "--unidiff-zero",
            patch_path,
        ],
        cwd=repo_copy,
        check=False,
    )


def _cell(text: str, width: int) -> str:
    """Pad text to width (simple ASCII assumption)."""
    s = str(text)
    if len(s) >= width:
        return s[:width]
    return s + " " * (width - len(s))


def print_result_table(target_id: str, success: bool, baseline: dict, patched: dict) -> None:
    """Print an orange-colored table as the final output block."""
    success_colored = f"{GREEN}TRUE{RESET}" if success else f"{RED}FALSE{RESET}"

    # Fixed widths for CI stability
    w_label = 10
    w_num = 7
    w_total = 7

    line1 = f"+{'-'*w_label}+{'-'*w_num}+{'-'*w_num}+{'-'*w_num}+{'-'*w_num}+{'-'*w_total}+"
    header = f"|{_cell('Repo', w_label)}|{_cell('Pass', w_num)}|{_cell('Fail', w_num)}|{_cell('Error', w_num)}|{_cell('Skip', w_num)}|{_cell('Total', w_total)}|"

    b_row = (
        f"|{_cell('Baseline', w_label)}|"
        f"{_cell(baseline.get('passed', 0), w_num)}|"
        f"{_cell(baseline.get('failed', 0), w_num)}|"
        f"{_cell(baseline.get('errors', 0), w_num)}|"
        f"{_cell(baseline.get('skipped', 0), w_num)}|"
        f"{_cell(baseline.get('total', 0), w_total)}|"
    )

    p_row = (
        f"|{_cell('Patched', w_label)}|"
        f"{_cell(patched.get('passed', 0), w_num)}|"
        f"{_cell(patched.get('failed', 0), w_num)}|"
        f"{_cell(patched.get('errors', 0), w_num)}|"
        f"{_cell(patched.get('skipped', 0), w_num)}|"
        f"{_cell(patched.get('total', 0), w_total)}|"
    )

    # Separate info lines
    info_w = len(line1) - 2
    info_line = f"+{'-'*info_w}+"

    tid_line = f"|{_cell('TARGET_ID: ' + target_id, info_w)}|"
    suc_line_raw = f"SUCCESS: "
    # Place colored TRUE/FALSE at end but keep line width stable
    suc_plain = suc_line_raw + ("TRUE" if success else "FALSE")
    # Build base padded line then inject colored token
    suc_base = _cell(suc_plain, info_w)
    # Replace last token with colored token (simple and safe)
    if success:
        suc_base = suc_base[:-4] + f"{GREEN}TRUE{RESET}"
    else:
        suc_base = suc_base[:-5] + f"{RED}FALSE{RESET}"
    suc_line = f"|{suc_base}|"

    print()
    print(f"{ORANGE}{BOLD}Test Result Summary{RESET}")
    print(f"{ORANGE}{line1}{RESET}")
    print(f"{ORANGE}{header}{RESET}")
    print(f"{ORANGE}{line1}{RESET}")
    print(f"{ORANGE}{b_row}{RESET}")
    print(f"{ORANGE}{p_row}{RESET}")
    print(f"{ORANGE}{line1}{RESET}")
    print(f"{ORANGE}{info_line}{RESET}")
    print(f"{ORANGE}{tid_line}{RESET}")
    print(f"{ORANGE}{suc_line}{RESET}")
    print(f"{ORANGE}{info_line}{RESET}")


def main() -> int:
    enable_ansi_on_windows()

    parser = argparse.ArgumentParser(description="Test Java repo baseline vs patched (filtered patch)")
    parser.add_argument("--target_id", required=True, help="Target identifier")
    parser.add_argument("--patch", required=True, help="Patch file path")
    parser.add_argument("--repo", required=True, help="Original repository path or git URL")
    parser.add_argument("--repo_copy", required=True, help="Temporary repository path for testing")

    args = parser.parse_args()

    target_id = args.target_id
    repo = args.repo
    repo_copy = args.repo_copy
    patch = args.patch

    filtered_patch_path: Optional[str] = None

    # This JSON is meant for batch scripts to parse
    result = {
        "target_id": target_id,
        "success": False,
        "reason": "",
        "baseline": {},
        "patched": {},
        "cmd": {
            "baseline_mvn_rc": None,
            "patched_mvn_rc": None,
            "git_apply_rc": None,
        },
        "paths": {
            "repo_copy": repo_copy,
            "filtered_patch": None,
        },
    }

    exit_code = 3  # default to exception

    try:
        print(f"[INFO] target_id={target_id}")
        print(f"[INFO] repo={repo}")
        print(f"[INFO] tmp_repo={repo_copy}")
        print(f"[INFO] patch={patch}")

        print("\n[STEP] Preparing temporary repository")
        prepare_tmp_repo(repo, repo_copy)

        print("\n[STEP] git init")
        git_init(repo_copy)

        print("\n[STEP] Baseline: mvn clean test")
        p1 = mvn_clean_test(repo_copy)
        print(p1.stdout)
        result["cmd"]["baseline_mvn_rc"] = p1.returncode

        baseline_stats = collect_test_stats(repo_copy)
        result["baseline"] = baseline_stats.to_dict()
        print("[INFO] Baseline surefire stats:", json.dumps(result["baseline"]))

        print("\n[STEP] Creating filtered patch (remove test changes)")
        filtered_patch_path = make_filtered_patch(patch)
        result["paths"]["filtered_patch"] = filtered_patch_path

        if filtered_patch_path is None:
            print("[WARN] Filtered patch has no non-test diffs. Skipping git apply and patched test.")
            patched_stats = baseline_stats
            result["cmd"]["git_apply_rc"] = 0
            result["cmd"]["patched_mvn_rc"] = p1.returncode
        else:
            print(f"[INFO] Filtered patch path: {filtered_patch_path}")

            print("\n[STEP] Applying filtered patch")
            ap = git_apply_patch(repo_copy, filtered_patch_path)
            print(ap.stdout)
            result["cmd"]["git_apply_rc"] = ap.returncode

            if ap.returncode != 0:
                result["success"] = False
                result["reason"] = "git_apply_failed"
                # Orange RESULT + red FALSE
                print(f"\n{ORANGE}[RESULT]{RESET} target_id={target_id} success={RED}FALSE{RESET}")
                # Patched equals baseline for table completeness
                result["patched"] = baseline_stats.to_dict()
                exit_code = 2
                return exit_code

            print("\n[STEP] Patched: mvn clean test")
            p2 = mvn_clean_test(repo_copy)
            print(p2.stdout)
            result["cmd"]["patched_mvn_rc"] = p2.returncode

            patched_stats = collect_test_stats(repo_copy)
            result["patched"] = patched_stats.to_dict()
            print("[INFO] Patched surefire stats:", json.dumps(result["patched"]))

        if not result["patched"]:
            result["patched"] = patched_stats.to_dict()

        # Success rule: patched passed >= baseline passed
        success = result["patched"]["passed"] >= result["baseline"]["passed"]
        result["success"] = success
        result["reason"] = "pass_ge_baseline" if success else "pass_lt_baseline"

        # Orange RESULT + green/red boolean
        if success:
            print(f"\n{ORANGE}[RESULT]{RESET} target_id={target_id} success={GREEN}TRUE{RESET}")
            exit_code = 0
        else:
            print(f"\n{ORANGE}[RESULT]{RESET} target_id={target_id} success={RED}FALSE{RESET}")
            exit_code = 1

        return exit_code

    except Exception as e:
        result["success"] = False
        result["reason"] = f"exception: {e}"
        print(f"\n[ERROR] {e}", file=sys.stderr)
        exit_code = 3
        return exit_code

    finally:
        # Print the orange table AFTER the RESULT line (as requested)
        try:
            # Ensure baseline/patched exist for table printing
            if not result["baseline"]:
                result["baseline"] = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total": 0}
            if not result["patched"]:
                result["patched"] = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total": 0}

            print_result_table(
                target_id=target_id,
                success=bool(result.get("success")),
                baseline=result["baseline"],
                patched=result["patched"],
            )
        except Exception:
            pass

        # Keep JSON as the very last line for batch scripts
        try:
            print("\n__RESULT_JSON__=" + json.dumps(result))
        except Exception:
            pass

        # Cleanup filtered patch
        if filtered_patch_path:
            try:
                Path(filtered_patch_path).unlink(missing_ok=True)
                tmp_patch_dir = Path("/tmp/patch")
                if tmp_patch_dir.exists() and tmp_patch_dir.is_dir():
                    try:
                        next(tmp_patch_dir.iterdir())
                    except StopIteration:
                        tmp_patch_dir.rmdir()
            except Exception:
                pass

        # Cleanup temp repo
        try:
            if Path(repo_copy).exists():
                shutil.rmtree(repo_copy, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())

    ##python run_mvn_test_one.py --target_id=CODEC-263_DBlog-master --patch=/VESTA/resource/patch_scripes/swe-agent_installed_patch/CODEC-263_DBlog-master.patch --repo=/VESTA/resource/CODEC-263/DBlog-master --repo_copy=/tmp/tmp_repo/CODEC-263/DBlog-master
