#!/usr/bin/env python3
"""Curate the manually reviewed cases where an upstream patch failed but its repair intent inspired a successful downstream repair."""

from __future__ import annotations

import csv
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULT_ROOT = HERE.parent
AVR_ROOT = RESULT_ROOT.parent
OUTPUT = HERE / "selfgen_patch_inspired_downstream_success_cases"

UPSTREAM_CSV = RESULT_ROOT / "upstream_downstream_comparison/matched_cve_details.csv"
BASE_MATRIX = HERE / "poc_merged/all_pocs_pass/cve_description_validation_matrix.csv"
SELF_MATRIX = HERE / "poc_merged/all_pocs_pass/with_selfgen_upstream_patch_matrix.csv"
EXPERIMENT = RESULT_ROOT / "with_selfgen_upstream_patch_results"
PIPELINE = EXPERIMENT / "nine_patch_validation_20260824_195016"

CASES = (
    {
        "folder": "01_agentless_CVE-2017-7957_cqrs-lottery-master",
        "tool": "agentless",
        "up_tool": "Agentless",
        "cve": "CVE-2017-7957",
        "target": "CVE-2017-7957_cqrs-lottery-master",
        "up_status": "Not Fixed",
        "base_status": "compile_error",
        "repo": AVR_ROOT / "upstream_dataset/upstream_repo_agentless/CVE-2017-7957/repo",
        "patch": EXPERIMENT / "normalized_patches/normalized_patches_agentless_20260821_214849/CVE-2017-7957_cqrs-lottery-master.patch",
        "baseline": PIPELINE / "baseline_run_01/summary.csv",
        "patched": PIPELINE / "01_normalized_patches_agentless_20260821_214849/patched/summary.csv",
        "Convert Void.TYPE to null inside XStream's Primitives.primitiveType"
        "Explicitly denyTypes(Void.TYPE) at the application's XStreamEventSerializer configuration layer"
        "analysis": (
            "The upstream patch had already identified that the dangerous point concerns the type"
            "resolution of void/Void.TYPE, but modifying the generic library's type-mapping layer still"
            "left it Not Fixed. The downstream project did not copy that implementation; it rejected Void.TYPE directly at the project's XStream initialisation point, achieving the same security intent in a more local way that better fits the downstream architecture."
        ),
    },
    {
        "folder": "02_appatch_CVE-2018-15756_mirage",
        "tool": "appatch",
        "up_tool": "Appatch",
        "cve": "CVE-2018-15756",
        "target": "CVE-2018-15756_mirage",
        "up_status": "Not Fixed",
        "base_status": "repair_failed",
        "repo": AVR_ROOT / "upstream_dataset/upstream_repo_appatch/CVE-2018-15756/repo",
        "patch": EXPERIMENT / "normalized_patches/normalized_patches_appatch_20260823_154146/CVE-2018-15756_mirage.patch",
        "baseline": PIPELINE / "baseline_run_01/summary.csv",
        "patched": PIPELINE / "02_normalized_patches_appatch_20260823_154146/patched/summary.csv",
        "Limit the number of HTTP Range headers in Spring's ResourceHttpRequestHandler"
        "Apply a project-level limit after Range parsing in Mirage's ResponseDelegate.file"
        "analysis": (
            "The upstream patch correctly pointed at the malicious excessive HTTP Range, but it modified the resource handler inside the Spring framework, so the"
            "validation result was still Not Fixed. Downstream Mirage has no such control flow, so the intent of limiting the number of Ranges was"
            "migrated to the ResponseDelegate.file boundary, rejecting requests with more than 100 Ranges after local parsing."
        ),
    },
    {
        "folder": "03_reinfix_CVE-2021-23899_json-sanitizer",
        "tool": "reinfix",
        "up_tool": "ReInFix",
        "cve": "CVE-2021-23899",
        "target": "CVE-2021-23899_json-sanitizer",
        "up_status": "Compilation Failed",
        "base_status": "repair_failed",
        "repo": AVR_ROOT / "upstream_dataset/upstream_repo_reinfix/CVE-2021-23899/repo",
        "patch": EXPERIMENT / "normalized_patches/normalized_patches_reinfix_20260821_214849/CVE-2021-23899_json-sanitizer.patch",
        "baseline": PIPELINE / "baseline_run_01/summary.csv",
        "patched": PIPELINE / "06_normalized_patches_reinfix_20260821_214849/patched/summary.csv",
        "Deeply rewrite the internal string state machine and escaping logic of JsonSanitizer"
        "Keep the library call and post-process the script and CDATA closing markers in the application wrapper layer"
        "analysis": (
            "The upstream patch had already focused on dangerous embedded-context output such as script and CDATA closing markers, but it fixed the"
            " issue by heavily rewriting the sanitizer's internal state machine, which ultimately resulted in Compilation Failed. The downstream fix keeps the original sanitize"
            " call and applies targeted escaping only at the output end of the application wrapper function, avoiding an invasive rewrite and passing validation."
        ),
    },
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def one_row(path: Path, target: str) -> dict[str, str]:
    selected = [row for row in read_csv(path) if row["target_id"] == target]
    if len(selected) != 1:
        raise ValueError(f"{path}: expected exactly one record for {target}, found {len(selected)}")
    return selected[0]


def git_diff(repo: Path) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", "HEAD", "--"],
        check=True,
        stdout=subprocess.PIPE,
    )
    if not result.stdout:
        raise ValueError(f"the upstream working tree has no exportable patch: {repo}")
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
            raise ValueError(f"{case['folder']}: upstream status changed to {up_status}")
        if base_status != case["base_status"]:
            raise ValueError(f"{case['folder']}: CVE-description-only status changed to {base_status}")
        if self_status != "success":
            raise ValueError(f"{case['folder']}: self-generated-upstream-patch status changed to {self_status}")

        baseline = one_row(case["baseline"], target)
        patched = one_row(case["patched"], target)
        case_dir = OUTPUT / case["folder"]
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "upstream_failed_patch.patch").write_bytes(git_diff(case["repo"]))
        shutil.copy2(case["patch"], case_dir / "downstream_successful_patch.patch")

        analysis = f"""# {case['up_tool']} / {case['cve']} / {target}

## Result evidence

- Upstream repair result: {up_status}
- Downstream "CVE description only" result: {base_status}
- Downstream "with self-generated upstream patch" result: {self_status} (all PoCs pass / AND criterion)
- Downstream validation: match_count {baseline['match_count']} -> {patched['match_count']}
- Post-patch compilation: {patched['compile_ok']}
- PoC signature: {patched['expected']}

## Repair-strategy comparison

- Upstream strategy: {case['up_strategy']}.
- Downstream strategy: {case['down_strategy']}.

## Conclusion

{case['analysis']}

## Accompanying material

- upstream_failed_patch.patch: exported from that tool's upstream repository working tree.
- downstream_successful_patch.patch: the corresponding normalized patch from "with_selfgen_upstream_patch_results".
"""
        (case_dir / "case_analysis.md").write_text(analysis, encoding="utf-8")
        summary.append(
            {
                "index": f"{number:02d}",
                "tool": case["up_tool"],
                "CVE": case["cve"],
                "target_id": target,
                "upstream_repair_status": up_status,
                "cve_description_only_status": base_status,
                "with_selfgen_upstream_patch_status": self_status,
                "baseline_match_count": baseline["match_count"],
                "patched_match_count": patched["match_count"],
                "upstream_strategy": case["up_strategy"],
                "downstream_strategy": case["down_strategy"],
            }
        )

    with (OUTPUT / "case_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    readme = """# Cases where the self-generated upstream patch failed but inspired a successful downstream repair

This directory collects 3 cases that were manually reviewed at the code level. Selection criteria:

1. The same tool's result on the upstream repository is not Fixed.
2. The same tool is success in the downstream "with self-generated upstream patch" experiment.
3. The strict "all PoCs pass (AND)" criterion is used.
4. After manual comparison, the upstream attempt and the downstream successful patch share the same security intent, but differ in where or how the fix is applied.

Each subdirectory contains the upstream failed patch, the downstream successful patch, and the case analysis.

Note: these cases support the mechanistic explanation that "a failed upstream attempt can still provide useful repair intent", but the validation
results themselves do not directly prove the model's internal "understanding" process.
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"Generated {len(CASES)} cases: {OUTPUT}")


if __name__ == "__main__":
    main()
