#!/usr/bin/env python3
"""Generate a case-by-case real-repository PoC review report for patches whose
modified files do not intersect the baseline's."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ERROR_DETAILS = ROOT / "localization_errors_detail.csv"
RUN_ROOT = Path(
    "/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果"
    "/nine_patch_validation_20260815_221755"
)
NORMALIZED_PATCH_ROOT = Path(
    "/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁"
)
BASELINE_PATCH_ROOT = Path(
    "/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline"
)
OUTPUT_DIR = ROOT / "real_repo_poc_review"

# Machine-readable keys are kept in summary.csv; the per-case reports spell them out.
CONCLUSION_LABELS = {
    "suspected_poc_support_function_localization_error": (
        "PoC supports a suspected function-localization error"
    ),
    "poc_validation_effective_not_a_localization_error": (
        "PoC verification effective (not a localization error)"
    ),
    "not_verified": "Not verified",
}
FUNCTION_PATH_LABELS = {
    "localized_to_unrelated_function": "Genuinely localized to an unrelated function",
    "localized_to_poc_related_function": "Localized to a PoC-related function",
}


def method_name(directory_name: str) -> str:
    match = re.fullmatch(r"normalized_patches_(.+?)_\d{8}_\d{6}", directory_name)
    if match is None:
        raise ValueError(f"Cannot identify the method from the patch directory name: {directory_name}")
    return match.group(1)


def index_summary(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    indexed: dict[str, dict] = {}
    for status, items in data["details"].items():
        for item in items:
            indexed[item["target_id"]] = {**item, "status": status}
    return indexed


def report_status(
    baseline: dict | None, patched: dict | None
) -> tuple[str, str, int | None, int | None]:
    """Return the conclusion, the explanation, the baseline match count and the
    post-patch match count."""
    if baseline is None or patched is None:
        return (
            "not_verified",
            "No corresponding real-repository PoC validation result is available.",
            None,
            None,
        )
    baseline_metrics = baseline["metrics"]
    patched_metrics = patched["metrics"]
    if not baseline_metrics.get("compile_ok"):
        return (
            "not_verified",
            "The baseline failed to compile, so the two cannot be compared.",
            None,
            None,
        )
    if not patched_metrics.get("compile_ok"):
        return (
            "not_verified",
            "The patch failed to compile or execute, so function localization cannot be "
            "judged from this.",
            None,
            None,
        )
    if baseline["mode"] != patched["mode"]:
        return (
            "not_verified",
            "The PoC detection modes differ, so the two cannot be compared.",
            None,
            None,
        )

    baseline_count = int(baseline_metrics.get("match_count", 0) or 0)
    patched_count = int(patched_metrics.get("match_count", 0) or 0)
    if patched_count < baseline_count:
        return (
            "poc_validation_effective_not_a_localization_error",
            "Although the files modified differ from the baseline, the real-repository PoC "
            "vulnerability match count did decrease, so the patch still hits the relevant "
            "code path.",
            baseline_count,
            patched_count,
        )
    relation = "unchanged" if patched_count == baseline_count else "increased"
    return (
        "suspected_poc_support_function_localization_error",
        f"The files modified differ from the baseline, and the real-repository PoC "
        f"vulnerability match count is {relation} ({baseline_count} -> {patched_count}). "
        f"This supports the localization missing the vulnerable path, but the patch semantics "
        f"still need manual review before it can be asserted as a definite "
        f"function-localization error.",
        baseline_count,
        patched_count,
    )


def manual_function_classification(method: str, target_id: str) -> tuple[str, str]:
    """Manual function-path review based on the original-repository PoC source, the
    inheritance relationships and the patch hunks."""
    unrelated: dict[tuple[str, str], str] = {
        (
            "agentless",
            "CODEC-270_DBlog-master",
        ): "The PoC only calls PasswordUtil.encrypt/decrypt in blog-core; the patch changes "
        "CredentialsMatcher in blog-admin, which the test path never instantiates.",
        (
            "agentless",
            "CVE-2017-7957_rpki-commons",
        ): "The PoC constructs ParentIdentitySerializer directly and calls deserialize; the "
        "patch changes ProvisioningCmsObjectParser, and the two are not on that call chain.",
        (
            "agentless",
            "CVE-2020-13956_wechat-ssm",
        ): "The PoC calls the static HTTP methods of HttpUtils directly; the patch only changes "
        "WeixinAuthController.calback, and the PoC never goes through the controller.",
        (
            "agentless",
            "CVE-2021-23900_OmegaTester",
        ): "The PoC calls HarConverter.toMyRequest directly; the patch only changes "
        "ReqCtrl.importRequest, and the PoC never goes through the web controller.",
        (
            "agentless",
            "CVE-2021-43859_rpki-commons",
        ): "The PoC calls ParentIdentitySerializer.deserialize directly; the patch changes "
        "ProvisioningCmsObjectParser, which belongs to a different provisioning payload path.",
        (
            "agentless",
            "CVE-2023-43642_flow",
        ): "The PoC constructs SnappyCoder directly and calls wrapOut; the patch changes "
        "CompressStreamer, which the PoC never goes through.",
        (
            "agentless",
            "IO-611_FastJoin",
        ): "The PoC only constructs soj.util.FileReader; the patch changes TopologyArgs and "
        "FileWriter, neither of which is on FileReader's test call path.",
        (
            "appatch",
            "CVE-2017-7957_rpki-commons",
        ): "The PoC uses ParentIdentitySerializer's own XStream initialization; the patch changes "
        "XStreamXmlSerializerBuilder, which that serializer construction path never calls.",
        (
            "appatch",
            "CVE-2021-43859_rpki-commons",
        ): "The PoC uses ParentIdentitySerializer; the patch changes payload paths such as "
        "PayloadParser and ProvisioningPayloadXmlSerializer, which do not take part in "
        "ParentIdentitySerializer.deserialize.",
        (
            "premm",
            "CVE-2019-10086_bean-query",
        ): "The PoC calls BeanPropertyMatcher.matches, which internally goes through "
        "DefaultNullValuePropertyValueGetter.getProperty; the patch changes PropertySelector, "
        "which the PoC neither constructs nor calls.",
        (
            "reinfix",
            "CVE-2019-10086_bean-query",
        ): "The PoC calls BeanPropertyMatcher.matches, which internally goes through "
        "DefaultNullValuePropertyValueGetter.getProperty; the patch changes PropertySelector, "
        "which the PoC neither constructs nor calls.",
        (
            "san2patch",
            "CVE-2019-10086_bean-query",
        ): "The PoC calls BeanPropertyMatcher.matches, which internally goes through "
        "DefaultNullValuePropertyValueGetter.getProperty; the patch changes PropertySelector, "
        "which the PoC neither constructs nor calls.",
        (
            "premm",
            "CVE-2020-13956_crawler-jsoup-maven",
        ): "The PoC calls CSDNLoginApater.getText/getRedirectLocation/setCookieStore; the patch "
        "only modifies the login flow in main, which does not affect these methods under test.",
        (
            "reinfix",
            "CVE-2020-13956_crawler-jsoup-maven",
        ): "The PoC calls CSDNLoginApater.getText/getRedirectLocation/setCookieStore; the patch "
        "only modifies the login flow in main, which does not affect these methods under test.",
        (
            "sweagent",
            "CVE-2022-29631_ucloud-java-sdk",
        ): "The PoC calls UFile.getFile, which uses HttpRequestUtil; the patch only adds "
        "SafeHttpRequestBuilder, a new class that the original repository never calls.",
    }
    key = (method, target_id)
    if key in unrelated:
        return "localized_to_unrelated_function", unrelated[key]
    related_evidence = {
        "CODEC-263_DBlog-master": "The PoC calls PasswordUtil directly; the patch also modifies "
        "PasswordUtil, which is the function under test.",
        "CODEC-270_BurpCrypto-master": "The PoC calls AesUtil directly; the patch also modifies "
        "AesUtil, which is the function under test.",
        "CODEC-270_DBlog-master": "The PoC calls PasswordUtil directly; this patch modifies "
        "PasswordUtil, which is the function under test.",
        "CVE-2015-2156_webbit": "The PoC directly tests the cookie behaviour of "
        "HttpRequestWrapper; the patch also modifies HttpRequestWrapper.",
        "CVE-2018-1002201_elasticsearch-maven-plugin": "The PoC calls ResolveElasticsearchStep "
        "via reflection; the patch also modifies that class.",
        "CVE-2019-10086_bean-query": "The PoC calls BeanPropertyMatcher.matches directly; this "
        "patch modifies BeanPropertyMatcher.",
        "CVE-2020-13956_wechat-ssm": "The PoC calls the static HTTP methods of HttpUtils "
        "directly; this patch modifies HttpUtils.",
        "CVE-2021-23899_OmegaTester": "The PoC calls HarConverter.toMyRequest directly; the "
        "patch also modifies that method.",
        "CVE-2021-23900_OmegaTester": "The PoC calls HarConverter.toMyRequest directly; the "
        "patch also modifies that method.",
        "CVE-2021-43859_rpki-commons": "The PoC's ParentIdentitySerializer extends "
        "IdentitySerializer; this patch modifies the superclass's XStream initialization chain.",
        "CVE-2022-29631_ucloud-java-sdk": "The PoC calls UFile.getFile, which calls "
        "HttpRequestUtil; this patch modifies that downstream HTTP request construction path.",
    }
    if target_id not in related_evidence:
        raise ValueError(f"No manual function-path conclusion was given: {method}/{target_id}")
    return "localized_to_poc_related_function", related_evidence[target_id]


def paths(value: str) -> list[str]:
    return value.split(" | ") if value else []


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- `{item}`" for item in items] or ["- (no path parsed)"]


def main() -> None:
    with ERROR_DETAILS.open(encoding="utf-8-sig", newline="") as handle:
        error_rows = list(csv.DictReader(handle))
    pipeline = json.loads((RUN_ROOT / "pipeline_summary.json").read_text(encoding="utf-8"))
    runs = {method_name(item["patch_directory"]): item for item in pipeline["patch_runs"]}
    summaries: dict[str, tuple[dict[str, dict], dict[str, dict]]] = {}
    for method, run in runs.items():
        baseline_summary = RUN_ROOT / Path(run["baseline_summary"]).parent.name / "summary.json"
        patched_summary = (
            RUN_ROOT
            / Path(run["patched_summary"]).parent.parent.name
            / "patched"
            / "summary.json"
        )
        summaries[method] = (index_summary(baseline_summary), index_summary(patched_summary))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    overview: list[dict[str, object]] = []
    for row in error_rows:
        method = row["method"]
        patch_name = row["patch_files"]
        target_id = patch_name.removesuffix(".patch")
        baseline, patched = summaries[method]
        conclusion, reason, baseline_count, patched_count = report_status(
            baseline.get(target_id), patched.get(target_id)
        )
        manual_conclusion, manual_evidence = manual_function_classification(method, target_id)
        generated_patch = NORMALIZED_PATCH_ROOT / runs[method]["patch_directory"] / patch_name
        baseline_patch = BASELINE_PATCH_ROOT / patch_name
        report_name = f"{method}__{target_id}.md"
        report_path = OUTPUT_DIR / report_name
        baseline_item = baseline.get(target_id)
        patched_item = patched.get(target_id)
        lines = [
            f"# {target_id} / {method}",
            "",
            "## Conclusion",
            "",
            f"**{CONCLUSION_LABELS[conclusion]}**",
            "",
            reason,
            "",
            "## Manual review of the original-repository PoC function path",
            "",
            f"**{FUNCTION_PATH_LABELS[manual_conclusion]}**",
            "",
            manual_evidence,
            "",
            "## File-localization comparison",
            "",
            f"- Generated patch: `{generated_patch}`",
            f"- Baseline patch: `{baseline_patch}`",
            "",
            "Files modified by the generated patch:",
            *bullet_lines(paths(row["generated_patch_modified_files"])),
            "",
            "Files modified by the baseline:",
            *bullet_lines(paths(row["baseline_modified_files"])),
            "",
            "## Real-repository PoC verification",
            "",
            f"- Detection mode: `{baseline_item['mode'] if baseline_item else 'none'}`",
            f"- Baseline status: `{baseline_item['status'] if baseline_item else 'none'}`",
            f"- Post-patch status: `{patched_item['status'] if patched_item else 'none'}`",
            f"- Baseline vulnerability match count: "
            f"`{baseline_count if baseline_count is not None else 'not_comparable'}`",
            f"- Post-patch vulnerability match count: "
            f"`{patched_count if patched_count is not None else 'not_comparable'}`",
            "",
        ]
        report_path.write_text("\n".join(lines), encoding="utf-8")
        overview.append(
            {
                "method": method,
                "target_id": target_id,
                "original_repo_function_path_conclusion": manual_conclusion,
                "manual_review_basis": manual_evidence,
                "conclusion": conclusion,
                "baseline_vuln_match_count": baseline_count if baseline_count is not None else "",
                "post_patch_vuln_match_count": patched_count if patched_count is not None else "",
                "per_case_report": report_name,
            }
        )

    overview_path = OUTPUT_DIR / "summary.csv"
    with overview_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(overview[0]))
        writer.writeheader()
        writer.writerows(overview)
    counts = Counter(str(item["conclusion"]) for item in overview)
    (OUTPUT_DIR / "README.md").write_text(
        "# Real-repository PoC localization review\n\n"
        f"This directory reviews, case by case, {len(overview)} patch instances whose modified "
        f"files do not intersect the baseline's.\n\n"
        f"- Original-repository PoC function path confirmed unrelated: "
        f"{sum(item['original_repo_function_path_conclusion'] == 'localized_to_unrelated_function' for item in overview)}\n"
        f"- Original-repository PoC function path related: "
        f"{sum(item['original_repo_function_path_conclusion'] == 'localized_to_poc_related_function' for item in overview)}\n"
        "\n"
        f"- PoC supports a suspected function-localization error: "
        f"{counts['suspected_poc_support_function_localization_error']}\n"
        f"- PoC verification effective (not a localization error): "
        f"{counts['poc_validation_effective_not_a_localization_error']}\n"
        f"- Not verified (compile/run error, or not comparable): {counts['not_verified']}\n"
        "\n"
        "The original-repository function-path conclusion is based on the classes/methods the "
        "PoC actually calls, the inheritance relationships and the patch hunks; PoC run counts "
        "serve only as supporting evidence.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()