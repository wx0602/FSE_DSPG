import os
import sys
import json
import logging
import subprocess
import uuid
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================== 配置区 ==========================

# repo_path -> patch_dir（patch_dir 里直接放该仓库的所有 *.patch）
TARGET_REPOS: Dict[str, str] = {
    "/home/user/AVR_JAVA_STUDY/VESTA_resource/resource/CVE-2017-7957/cqrs-lottery-master": "/home/user/AVR_JAVA_STUDY/agentless/Agentless/results/poc-bench-lite/repair_diff_patch",
    "/path/to/repos/repoB": "/path/to/patches/bb",
}

LOG_DIR = "./logs"
MVN_TIMEOUT = 3600

# 不同仓库并行度
MAX_WORKERS = 4

# 是否递归扫描 patch_dir 下的 patch
PATCH_RECURSIVE = False  # True: patch_dir/**/*.patch

COMPILE_ERROR_KEYWORDS = [
    "COMPILATION ERROR",
    "Compilation failure",
    "cannot find symbol",
    "error: package",
    "Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin",
]

MVN_COMMANDS: List[List[str]] = [
    ["mvn", "clean", "install", "-DskipTests"],
    ["mvn", "clean", "install", "-DskipTests", "-Dgpg.skip=true"],
]

# ===========================================================


# ========================== 控制台输出（线程安全 + 颜色）==========================

print_lock = threading.Lock()
GREEN = "\033[32m"
RESET = "\033[0m"

def console_print(msg: str) -> None:
    with print_lock:
        print(msg, flush=True)

def console_sep() -> None:
    console_print("====")

def green_text(s: str) -> str:
    return f"{GREEN}{s}{RESET}"


# ========================== 统计结构 ==========================

@dataclass
class PatchStats:
    total: int = 0
    success: int = 0
    fail: int = 0
    compile_fail: int = 0

    def add(self, other: "PatchStats") -> None:
        self.total += other.total
        self.success += other.success
        self.fail += other.fail
        self.compile_fail += other.compile_fail


# ========================== 通用工具 ==========================

def sanitize_filename(name: str) -> str:
    bad = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for b in bad:
        name = name.replace(b, "_")
    return name

def is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))

def find_patches_in_dir(patch_dir: str) -> List[Path]:
    d = Path(patch_dir)
    if not d.is_dir():
        return []
    return sorted(d.rglob("*.patch")) if PATCH_RECURSIVE else sorted(d.glob("*.patch"))

def is_compile_error(log_file: str) -> bool:
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return any(k in content for k in COMPILE_ERROR_KEYWORDS)
    except Exception:
        return False


# ========================== 每仓库独立 logger ==========================

def create_repo_logger(repo_abs: str) -> Tuple[logging.Logger, str]:
    os.makedirs(LOG_DIR, exist_ok=True)
    repo_name = sanitize_filename(os.path.basename(repo_abs) or "repo")
    rand = uuid.uuid4().hex[:8]
    log_file = os.path.join(LOG_DIR, f"{repo_name}_{rand}.json.log")

    logger_name = f"RepoLogger::{repo_abs}::{rand}"
    lg = logging.getLogger(logger_name)
    lg.setLevel(logging.INFO)
    lg.propagate = False
    lg.handlers.clear()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(message)s"))
    lg.addHandler(fh)

    return lg, log_file

def log_event(logger: logging.Logger, level: str, **fields) -> None:
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "level": level,
        **fields
    }
    logger.log(
        logging.ERROR if level == "ERROR" else logging.INFO,
        json.dumps(record, ensure_ascii=False)
    )


# ========================== 命令执行 ==========================

def run_command(
    logger: logging.Logger,
    cmd: List[str],
    cwd: str,
    output_file: Optional[str] = None
) -> bool:
    try:
        stdout_target = subprocess.PIPE
        stderr_target = subprocess.STDOUT
        f = None

        if output_file:
            out_dir = os.path.dirname(output_file)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            f = open(output_file, "w", encoding="utf-8")
            stdout_target = f
            stderr_target = f

        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=stdout_target,
            stderr=stderr_target,
            text=True,
            timeout=MVN_TIMEOUT
        )

        if f:
            f.close()

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        log_event(logger, "ERROR", step="command_timeout", cmd=" ".join(cmd), cwd=cwd, timeout_sec=MVN_TIMEOUT)
        return False
    except Exception as e:
        log_event(logger, "ERROR", step="command_exception", cmd=" ".join(cmd), cwd=cwd, error=str(e))
        return False


# ========================== 核心逻辑（仓库内串行）==========================

def detect_working_maven_cmd(logger: logging.Logger, repo_abs: str) -> Optional[List[str]]:
    for cmd in MVN_COMMANDS:
        log_event(logger, "INFO", repo=repo_abs, step="initial_mvn_build_try", cmd=" ".join(cmd))
        if run_command(logger, cmd, repo_abs):
            log_event(logger, "INFO", repo=repo_abs, step="initial_mvn_build", result="success", cmd=" ".join(cmd))
            return cmd
    log_event(logger, "ERROR", repo=repo_abs, step="initial_mvn_build", result="fail", reason="all_mvn_commands_failed")
    return None


def process_repo(repo_path: str, patch_dir: str) -> Tuple[str, PatchStats, str]:
    """
    返回：(repo_abs, stats, repo_log_file)
    """
    repo_abs = os.path.abspath(repo_path)
    patch_dir_abs = os.path.abspath(patch_dir)
    repo_name = os.path.basename(repo_abs)

    repo_logger, repo_log_file = create_repo_logger(repo_abs)
    log_event(repo_logger, "INFO", repo=repo_abs, step="repo_start", patch_dir=patch_dir_abs, repo_log_file=repo_log_file)

    if not is_git_repo(repo_abs):
        log_event(repo_logger, "ERROR", repo=repo_abs, step="git_check", result="skip", reason="not_a_git_repo")
        # 控制台也打一条
        console_sep()
        console_print(f"[PATCH] repo={repo_name} patch=<N/A> result=SKIP reason=not_a_git_repo")
        return repo_abs, PatchStats(), repo_log_file

    patches = find_patches_in_dir(patch_dir_abs)
    if not patches:
        log_event(repo_logger, "ERROR", repo=repo_abs, step="patch_scan", result="skip",
                  reason="no_patch_found_or_patch_dir_missing", patch_dir=patch_dir_abs, recursive=PATCH_RECURSIVE)
        console_sep()
        console_print(f"[PATCH] repo={repo_name} patch=<N/A> result=SKIP reason=no_patch_found patch_dir={patch_dir_abs}")
        return repo_abs, PatchStats(), repo_log_file

    stats = PatchStats(total=len(patches))
    log_event(repo_logger, "INFO", repo=repo_abs, step="patch_scan", result="found",
              patch_count=len(patches), patch_dir=patch_dir_abs, recursive=PATCH_RECURSIVE)

    success_cmd = detect_working_maven_cmd(repo_logger, repo_abs)
    if not success_cmd:
        log_event(repo_logger, "ERROR", repo=repo_abs, step="repo_abort", reason="initial_mvn_build_failed",
                  patch_count=len(patches))
        # 控制台提示仓库无法继续
        console_sep()
        console_print(f"[PATCH] repo={repo_name} patch=<N/A> result=ABORT reason=initial_mvn_build_failed")
        log_event(repo_logger, "INFO", repo=repo_abs, step="repo_summary", **asdict(stats))
        log_event(repo_logger, "INFO", repo=repo_abs, step="repo_end")
        return repo_abs, stats, repo_log_file

    for patch in patches:
        patch_name = patch.name
        patch_safe = sanitize_filename(patch.stem)

        log_event(repo_logger, "INFO", repo=repo_abs, patch=patch_name, step="patch_test_start",
                  patch_file=str(patch), mvn_cmd=" ".join(success_cmd))

        # 1) apply
        if not run_command(repo_logger, ["git", "apply", str(patch)], repo_abs):
            stats.fail += 1
            log_event(repo_logger, "ERROR", repo=repo_abs, patch=patch_name, step="git_apply",
                      result="fail", patch_file=str(patch))

            console_sep()
            console_print(f"[PATCH] repo={repo_name} patch={patch_name} result=FAIL stage=git_apply")
            continue

        # 2) mvn after patch -> txt
        build_log = os.path.join(repo_abs, f"mvn_after_{patch_safe}_{datetime.now():%Y%m%d_%H%M%S}.txt")
        build_ok = run_command(repo_logger, success_cmd, repo_abs, build_log)

        if build_ok:
            stats.success += 1
            log_event(repo_logger, "INFO", repo=repo_abs, patch=patch_name, step="mvn_build_after_patch",
                      result="success", log_file=build_log, mvn_cmd=" ".join(success_cmd))

            console_sep()
            console_print(f"[PATCH] repo={repo_name} patch={patch_name} result=PASS log={build_log}")
        else:
            stats.fail += 1
            if is_compile_error(build_log):
                stats.compile_fail += 1
                error_type = "compile_error"
            else:
                error_type = "other_error"

            log_event(repo_logger, "ERROR", repo=repo_abs, patch=patch_name, step="mvn_build_after_patch",
                      result="fail", error_type=error_type, log_file=build_log, mvn_cmd=" ".join(success_cmd))

            console_sep()
            console_print(f"[PATCH] repo={repo_name} patch={patch_name} result=FAIL type={error_type} log={build_log}")

        # 3) revert
        if not run_command(repo_logger, ["git", "apply", "-R", str(patch)], repo_abs):
            stats.fail += 1
            log_event(repo_logger, "ERROR", repo=repo_abs, patch=patch_name, step="git_revert",
                      result="fail", reason="manual_intervention_required_stop_repo", patch_file=str(patch))

            console_sep()
            console_print(f"[PATCH] repo={repo_name} patch={patch_name} result=ABORT stage=git_revert_failed (stop repo)")
            break

        log_event(repo_logger, "INFO", repo=repo_abs, patch=patch_name, step="patch_test_end", result="done")

    log_event(repo_logger, "INFO", repo=repo_abs, step="repo_summary", **asdict(stats))
    log_event(repo_logger, "INFO", repo=repo_abs, step="repo_end")
    return repo_abs, stats, repo_log_file


# ========================== main（仓库间并行）==========================

def main() -> None:
    console_print(f"[START] repos={len(TARGET_REPOS)} max_workers={MAX_WORKERS}")

    jobs: List[Tuple[str, str]] = []
    for repo_path, patch_dir in TARGET_REPOS.items():
        if not os.path.isdir(repo_path):
            console_print(f"[SKIP] invalid repo_path: {repo_path}")
            continue
        if not os.path.isdir(patch_dir):
            console_print(f"[SKIP] invalid patch_dir: {patch_dir} for repo: {repo_path}")
            continue
        jobs.append((repo_path, patch_dir))

    overall = PatchStats()
    per_repo: Dict[str, Tuple[PatchStats, str]] = {}  # repo_abs -> (stats, repo_log_file)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(process_repo, repo, pdir): (repo, pdir) for repo, pdir in jobs}

        for fut in as_completed(future_map):
            repo, _ = future_map[fut]
            repo_abs = os.path.abspath(repo)
            try:
                repo_abs_ret, repo_stats, repo_log_file = fut.result()
                per_repo[repo_abs_ret] = (repo_stats, repo_log_file)
                overall.add(repo_stats)
            except Exception as e:
                console_print(f"[ERROR] repo={repo_abs} thread_exception={e!s}")

    # ===== 总总结：按仓库列举（绿色）=====
    console_print(green_text("==== REPO SUMMARY (GREEN) ===="))
    for repo_abs in sorted(per_repo.keys()):
        repo_stats, repo_log_file = per_repo[repo_abs]
        repo_name = os.path.basename(repo_abs)
        line = (f"[REPO] repo={repo_name} total={repo_stats.total} "
                f"fail={repo_stats.fail} compile_fail={repo_stats.compile_fail} "
                f"repo_log={repo_log_file}")
        console_print(green_text(line))

    console_print(green_text(
        f"[OVERALL] total={overall.total} success={overall.success} fail={overall.fail} compile_fail={overall.compile_fail}"
    ))
    console_print("[END]")


if __name__ == "__main__":
    main()
