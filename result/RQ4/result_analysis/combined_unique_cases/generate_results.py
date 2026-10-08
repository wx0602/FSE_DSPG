#!/usr/bin/env python3
"""找出前三组失败、但“自生成上游补丁+漏洞链”成功的工具—补丁对。"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
PATCH_OUT = OUT / "successful_patches"

MATRICES = {
    'vuln_chain'' / "with_vuln_chain_validation_matrix.csv",
    'cve_description'ption'OT / "cve_description_validation_matrix.csv",
    'selfgen_upstream_patch''_selfgen_upstream_patch_matrix.csv",
    'selfgen_upstream_patch_plus_vuln_chain'hain'_upstream_patch_and_vuln_chain_matrix.csv",
}

PRIOR_GROUPS = ('vuln_chain''描述'cve_description'ption'")'selfgen_upstream_patch''gen_upstream_patch_plus_vuln_chain'hain'ile(r"^normalized_patches_(?P<tool>.+?)_\d{8}_\d{6}$")


def load_matrix(path: Path) -> tuple[list[str], dict[tuple[str, str], str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"矩阵表头不合法：{path}")
        tools = reader.fieldnames[1:]
        result: dict[tuple[str, str], str] = {}
        for row in reader:
            target_id = row["target_id"]
            for tool in tools:
                key = (target_id, tool)
                if key in result:
                    raise ValueError(f"矩阵中出现重复键 {key}：{path}")
                result[key] = row[tool]
    return tools, result


def latest_complete_pipeline(experiment_dir: Path) -> tuple[Path, dict]:
    complete: list[tuple[Path, dict]] = []
    for pipeline_path in sorted(
        experiment_dir.glob("nine_patch_validation_*/pipeline_summary.json")
    ):
        pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))
        runs = pipeline.get("patch_runs", [])
        if runs and all(
            (
                pipeline_path.parent
                / f"{int(run['run_number']):02d}_{run['patch_directory']}"
                / "patched"
                / "summary.json"
            ).is_file()
            for run in runs
        ):
            complete.append((pipeline_path, pipeline))
    if not complete:
        raise RuntimeError(f"没有完整验证批次：{experiment_dir}")
    return complete[-1]


def combined_patch_dirs() -> tuple[Path, dict[str, str]]:
    experiment_dir = ROOT / 'selfgen_upstream_patch_and_vuln_chain_validation'atest_complete_pipeline(experiment_dir)
    tool_dirs: dict[str, str] = {}
    for run in pipeline["patch_runs"]:
        directory = str(run["patch_directory"])
        match = TOOL_DIR_RE.fullmatch(directory)
        if not match:
            raise ValueError(f"无法从补丁目录提取工具名：{directory}")
        tool_dirs[match.group("tool")] = directory
    return pipeline_path, tool_dirs


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    loaded = {name: load_matrix(path) for name, path in MATRICES.items()}
    tools = loaded[COMBINED_GROUP][0]
    if any(group_tools != tools for group_tools, _ in loaded.values()):
        raise ValueError("四张矩阵的工具列或工具顺序不一致")

    matrices = {name: values for name, (_, values) in loaded.items()}
    key_sets = {name: set(values) for name, values in matrices.items()}
    reference_keys = key_sets[COMBINED_GROUP]
    if any(keys != reference_keys for keys in key_sets.values()):
        raise ValueError("四张矩阵的 target_id × 工具键集合不一致")

    strict_keys = sorted(
        key
        for key in reference_keys
        if matrices[COMBINED_GROUP][key] == "success"
        and all(matrices[group][key] == 'repair_failed''up in PRIOR_GROUPS)
    )
    broad_keys = sorted(
        key
        for key in reference_keys
        if matrices[COMBINED_GROUP][key] == "success"
        and all(matrices[group][key] != "success" for group in PRIOR_GROUPS)
    )

    pipeline_path, tool_dirs = combined_patch_dirs()
    PATCH_OUT.mkdir(parents=True, exist_ok=True)
    strict_rows: list[dict[str, str]] = []
    expected_copies: set[str] = set()
    for index, (target_id, tool) in enumerate(strict_keys, start=1):
        source = (
            ROOT
            / 'selfgen_upstream_patch_and_vuln_chain_validation'es' / tool_dirs[tool]
            / f"{target_id}.patch"
        )
        if not source.is_file():
            raise FileNotFoundError(f"成功补丁不存在：{source}")
        copied_name = f"{tool}__{target_id}.patch"
        expected_copies.add(copied_name)
        copied = PATCH_OUT / copied_name
        shutil.copy2(source, copied)
        data = source.read_bytes()
        strict_rows.append(
            {
                'index'(index),
                "target_id": target_id,
                'tool',
                'vuln_chain''ices["漏洞链"]'vuln_chain'', tool)],
                'cve_description'ption'trices["CVE'cve_description'ption't_id, tool)],
                'selfgen_upstream_patch''成上游补丁"][(ta'selfgen_upstream_patch''          'selfgen_upstream_patch_plus_vuln_chain'hain'OUP][
                    (target_id, tool)
                ],
                "成功补丁副本": f"successful_patches/{copied_name}",
                "成功补丁源路径": str(source.relative_to(ROOT)),
                "补丁SHA256": hashlib.sha256(data).hexdigest(),
                "补丁字节数": str(len(data)),
            }
        )

    # 防止重新生成后残留已经不属于严格结果的旧补丁副本。
    for copied in PATCH_OUT.glob("*.patch"):
        if copied.name not in expected_copies:
            copied.unlink()

    strict_fields = [
        'index'     "target_id",
        'tool'    'vuln_chain''    'cve_description'ption'      'selfgen_upstream_patch''fgen_upstream_patch_plus_vuln_chain'hain'      "成功补丁源路径",
        "补丁SHA256",
        "补丁字节数",
    ]
    write_csv(OUT / "all_cases_strict.csv", strict_rows, strict_fields)

    broad_rows = []
    strict_set = set(strict_keys)
    for index, (target_id, tool) in enumerate(broad_keys, start=1):
        broad_rows.append(
            {
                'index'(index),
                "target_id": target_id,
                'tool',
                "是否也属于严格口径": "是" if (target_id,'yes') in strict_set else "否",
               'no'_chain''ices["漏洞链"]'vuln_chain'', tool)],
                'cve_description'ption'trices["CVE'cve_description'ption't_id, tool)],
                'selfgen_upstream_patch''成上游补丁"][(ta'selfgen_upstream_patch''          'selfgen_upstream_patch_plus_vuln_chain'hain'OUP][
                    (target_id, tool)
                ],
            }
        )
    broad_fields = [
        'index'     "target_id",
        'tool'    "是否也属于严格口径",
        'vuln_chain''    'cve_description'ption'      'selfgen_upstream_patch''fgen_upstream_patch_plus_vuln_chain'hain'OUT / "appendix_first_three_groups_all_fail.csv", broad_rows, broad_fields)

    tool_counts = Counter(tool for _, tool in strict_keys)
    case_lines = "\n".join(
        f"{index}. `{tool}` × `{target_id}.patch`"
        for index, (target_id, tool) in enumerate(strict_keys, start=1)
    )
    tool_count_text = "、".join(
        f"{tool} {count} 对" for tool, count in sorted(tool_counts.items())
    )
    source_lines = "\n".join(
        f"- `{name}`：`{path.name}`" for name, path in MATRICES.items()
    )
    readme = f"""# 三组修复失败、组合组修复成功的 case

## 结论

严格口径下共找到 **{len(strict_keys)} 个 `<工具, 补丁>` 对**。

严格判定条件：

- `with_vuln_chain_validation_matrix.csv == 修复失败`
- `cve_description_validation_matrix.csv == 修复失败`
- `with_selfgen_upstream_patch_matrix.csv == 修复失败`
- `with_selfgen_upstream_patch_and_vuln_chain_matrix.csv == success`

四张矩阵均有 {len(reference_keys)} 个相同的 `target_id × 工具` 键（{len(reference_keys) // len(tools)} 个 target、{len(tools)} 个工具），因此不存在因缺行或缺工具造成的漏配。

## 所有严格口径 case

{case_lines}

按工具统计：{tool_count_text}。

详细的四组状态、成功补丁路径、SHA-256 和文件大小见 `all_cases_strict.csv`；对应成功补丁已复制到 `successful_patches/`。

## 宽口径附录

如果把 `编译错误` 和 `empty` 也算作“没有修复成功”，则共 {len(broad_keys)} 对。完整清单见 `appendix_first_three_groups_all_fail.csv`，其中用“是否也属于严格口径”标出了上述 {len(strict_keys)} 对。

## 数据来源与复现

{source_lines}

组合实验采用最新的完整批次：`{pipeline_path.relative_to(ROOT)}`。

在本目录执行 `python3 generate_results.py` 可重新计算清单并刷新补丁副本。脚本会校验四张矩阵的工具列和全部键完全一致。
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    print(f"严格口径: {len(strict_keys)} 对")
    print(f"宽口径: {len(broad_keys)} 对")
    print(f"结果目录: {OUT}")


if __name__ == "__main__":
    main()
