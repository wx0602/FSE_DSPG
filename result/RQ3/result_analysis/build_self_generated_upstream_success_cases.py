#!/usr/bin/env python3
"""整理“上游补丁失败，但其修复意图启发下游修复成功”的人工复核案例。"""

from __future__ import annotations

import csv
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULT_ROOT = HERE.parent
AVR_ROOT = RESULT_ROOT.parent
OUTPUT = HERE / "自生成上游补丁启发下游修复成功案例"

UPSTREAM_CSV = RESULT_ROOT / "上下游修复对比/matched_cve_details.csv"
BASE_MATRIX = HERE / "poc合并/所有PoC都通过/CVE 描述验证结果_矩阵.csv"
SELF_MATRIX = HERE / "poc合并/所有PoC都通过/带自生成上游补丁验证结果_矩阵.csv"
EXPERIMENT = RESULT_ROOT / "带自生成上游补丁验证结果"
PIPELINE = EXPERIMENT / "nine_patch_validation_20260824_195016"

CASES = (
    {
        "folder": "01_agentless_CVE-2017-7957_cqrs-lottery-master",
        "tool": "agentless",
        "up_tool": "Agentless",
        "cve": "CVE-2017-7957",
        "target": "CVE-2017-7957_cqrs-lottery-master",
        "up_status": "Not Fixed",
        "base_status": "编译错误",
        "repo": AVR_ROOT / "upstream_dataset/upstream_repo_agentless/CVE-2017-7957/repo",
        "patch": EXPERIMENT / "正则化的补丁/normalized_patches_agentless_20260821_214849/CVE-2017-7957_cqrs-lottery-master.patch",
        "baseline": PIPELINE / "baseline_run_01/summary.csv",
        "patched": PIPELINE / "01_normalized_patches_agentless_20260821_214849/patched/summary.csv",
        "up_strategy": "在 XStream 的 Primitives.primitiveType 内部将 Void.TYPE 转为 null",
        "down_strategy": "在应用的 XStreamEventSerializer 配置层显式 denyTypes(Void.TYPE)",
        "analysis": (
            "上游补丁已经识别到危险点与 void/Void.TYPE 的类型解析有关，但在通用库的类型映射层"
            "修改后仍被判定为 Not Fixed。下游没有照搬该实现，而是在项目的 XStream 初始化位置"
            "直接拒绝 Void.TYPE，以更局部、更适合下游架构的方式实现了同一安全意图。"
        ),
    },
    {
        "folder": "02_appatch_CVE-2018-15756_mirage",
        "tool": "appatch",
        "up_tool": "Appatch",
        "cve": "CVE-2018-15756",
        "target": "CVE-2018-15756_mirage",
        "up_status": "Not Fixed",
        "base_status": "修复失败",
        "repo": AVR_ROOT / "upstream_dataset/upstream_repo_appatch/CVE-2018-15756/repo",
        "patch": EXPERIMENT / "正则化的补丁/normalized_patches_appatch_20260823_154146/CVE-2018-15756_mirage.patch",
        "baseline": PIPELINE / "baseline_run_01/summary.csv",
        "patched": PIPELINE / "02_normalized_patches_appatch_20260823_154146/patched/summary.csv",
        "up_strategy": "在 Spring ResourceHttpRequestHandler 中限制 HTTP Range 数量",
        "down_strategy": "在 Mirage ResponseDelegate.file 的 Range 解析后执行项目级数量限制",
        "analysis": (
            "上游补丁正确指向恶意的过量 HTTP Range，但它修改的是 Spring 框架中的资源处理器，"
            "验证结果仍为 Not Fixed。下游 Mirage 没有相同控制流，因此把限制 Range 数量的意图"
            "迁移到 ResponseDelegate.file 边界，在本地解析后拒绝超过 100 个 Range 的请求。"
        ),
    },
    {
        "folder": "03_reinfix_CVE-2021-23899_json-sanitizer",
        "tool": "reinfix",
        "up_tool": "ReInFix",
        "cve": "CVE-2021-23899",
        "target": "CVE-2021-23899_json-sanitizer",
        "up_status": "Compilation Failed",
        "base_status": "修复失败",
        "repo": AVR_ROOT / "upstream_dataset/upstream_repo_reinfix/CVE-2021-23899/repo",
        "patch": EXPERIMENT / "正则化的补丁/normalized_patches_reinfix_20260821_214849/CVE-2021-23899_json-sanitizer.patch",
        "baseline": PIPELINE / "baseline_run_01/summary.csv",
        "patched": PIPELINE / "06_normalized_patches_reinfix_20260821_214849/patched/summary.csv",
        "up_strategy": "深入改写 JsonSanitizer 内部字符串状态机和转义逻辑",
        "down_strategy": "保留库调用，在应用封装层后处理 script 与 CDATA 结束标记",
        "analysis": (
            "上游补丁已聚焦于 script 和 CDATA 结束标记等嵌入上下文危险输出，但通过大幅改写"
            " sanitizer 内部状态机来修复，最终导致 Compilation Failed。下游保留原有 sanitize"
            " 调用，只在应用封装函数的输出端做针对性转义，从而避免侵入式改造并通过验证。"
        ),
    },
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def one_row(path: Path, target: str) -> dict[str, str]:
    selected = [row for row in read_csv(path) if row["target_id"] == target]
    if len(selected) != 1:
        raise ValueError(f"{path}: {target} 的记录数为 {len(selected)}")
    return selected[0]


def git_diff(repo: Path) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", "HEAD", "--"],
        check=True,
        stdout=subprocess.PIPE,
    )
    if not result.stdout:
        raise ValueError(f"上游工作树没有可导出的补丁：{repo}")
    return result.stdout


def main() -> None:
    upstream = {
        (row["cve"], row["tool"]): row["upstream_status"]
        for row in read_csv(UPSTREAM_CSV)
    }
    base = {row["target_id"]: row for row in read_csv(BASE_MATRIX)}
    self_matrix = {row["target_id"]: row for row in read_csv(SELF_MATRIX)}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, str]] = []

    for number, case in enumerate(CASES, start=1):
        target = case["target"]
        tool = case["tool"]
        up_status = upstream[(case["cve"], case["up_tool"])]
        base_status = base[target][tool]
        self_status = self_matrix[target][tool]
        if up_status != case["up_status"]:
            raise ValueError(f"{case['folder']}: 上游状态变为 {up_status}")
        if base_status != case["base_status"]:
            raise ValueError(f"{case['folder']}: 仅CVE描述状态变为 {base_status}")
        if self_status != "success":
            raise ValueError(f"{case['folder']}: 自生成上游补丁状态变为 {self_status}")

        baseline = one_row(case["baseline"], target)
        patched = one_row(case["patched"], target)
        case_dir = OUTPUT / case["folder"]
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "上游失败补丁.patch").write_bytes(git_diff(case["repo"]))
        shutil.copy2(case["patch"], case_dir / "下游成功补丁.patch")

        analysis = f"""# {case['up_tool']} / {case['cve']} / {target}

## 结果证据

- 上游修复结果：{up_status}
- 下游“仅 CVE 描述”结果：{base_status}
- 下游“增加自生成上游补丁”结果：{self_status}（所有 PoC 都通过/AND 口径）
- 下游验证：match_count {baseline['match_count']} -> {patched['match_count']}
- 补丁后编译：{patched['compile_ok']}
- PoC 特征：{patched['expected']}

## 修复策略对比

- 上游策略：{case['up_strategy']}。
- 下游策略：{case['down_strategy']}。

## 结论

{case['analysis']}

## 随附材料

- 上游失败补丁.patch：从该工具的上游仓库工作树导出。
- 下游成功补丁.patch：来自“带自生成上游补丁验证结果”的对应正则化补丁。
"""
        (case_dir / "案例分析.md").write_text(analysis, encoding="utf-8")
        summary.append(
            {
                "编号": f"{number:02d}",
                "工具": case["up_tool"],
                "CVE": case["cve"],
                "target_id": target,
                "上游修复状态": up_status,
                "仅CVE描述状态": base_status,
                "增加自生成上游补丁状态": self_status,
                "baseline_match_count": baseline["match_count"],
                "patched_match_count": patched["match_count"],
                "上游策略": case["up_strategy"],
                "下游策略": case["down_strategy"],
            }
        )

    with (OUTPUT / "案例汇总.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    readme = """# 自生成上游补丁失败、但启发下游修复成功的案例

本目录收录 3 个经过代码级人工复核的案例。筛选条件：

1. 同一工具在上游仓库的结果不是 Fixed。
2. 同一工具在下游“增加自生成上游补丁”实验中为 success。
3. 使用严格的“所有 PoC 都通过（AND）”口径。
4. 人工比较后，上游尝试与下游成功补丁具有一致的安全意图，但修改落点或实现策略不同。

每个子目录包含上游失败补丁、下游成功补丁和案例分析。

注意：这些案例支持“上游失败尝试仍可提供有用修复意图”的机制解释，但验证结果本身不能
直接证明模型内部的“理解”过程。
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"已生成 {len(CASES)} 个案例：{OUTPUT}")


if __name__ == "__main__":
    main()
