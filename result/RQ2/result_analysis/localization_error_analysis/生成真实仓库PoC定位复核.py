#!/usr/bin/env python3
"""为文件路径不重合的补丁生成逐条真实仓库 PoC 复核报告。"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ERROR_DETAILS = ROOT / "定位错误统计" / "定位错误明细.csv"
RUN_ROOT = ROOT / "nine_patch_validation_20260815_221755"
BASELINE_PATCH_ROOT = Path(
    "/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline"
)
OUTPUT_DIR = ROOT / "定位错误统计" / "真实仓库PoC定位复核"


def method_name(directory_name: str) -> str:
    match = re.fullmatch(r"normalized_patches_(.+?)_\d{8}_\d{6}", directory_name)
    if match is None:
        raise ValueError(f"无法从补丁目录名识别方法：{directory_name}")
    return match.group(1)


def index_summary(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    indexed: dict[str, dict] = {}
    for status, items in data["details"].items():
        for item in items:
            indexed[item["target_id"]] = {**item, "status": status}
    return indexed


def report_status(baseline: dict | None, patched: dict | None) -> tuple[str, str, int | None, int | None]:
    """返回结论、说明、baseline 匹配数、补丁后匹配数。"""
    if baseline is None or patched is None:
        return "未验证", "缺少对应的真实仓库 PoC 验证结果。", None, None
    baseline_metrics = baseline["metrics"]
    patched_metrics = patched["metrics"]
    if not baseline_metrics.get("compile_ok"):
        return "未验证", "baseline 未能编译，不能比较。", None, None
    if not patched_metrics.get("compile_ok"):
        return "未验证", "补丁编译或执行异常，不能据此判断函数定位。", None, None
    if baseline["mode"] != patched["mode"]:
        return "未验证", "两侧 PoC 检测模式不同，不能比较。", None, None

    baseline_count = int(baseline_metrics.get("match_count", 0) or 0)
    patched_count = int(patched_metrics.get("match_count", 0) or 0)
    if patched_count < baseline_count:
        return (
            "PoC验证有效（非定位错误）",
            "虽然修改文件与 baseline 不同，但真实仓库 PoC 的漏洞匹配数已降低，补丁仍命中了相关代码路径。",
            baseline_count,
            patched_count,
        )
    relation = "相同" if patched_count == baseline_count else "升高"
    return (
        "PoC支持疑似函数定位错误",
        f"修改文件与 baseline 不同，且真实仓库 PoC 的漏洞匹配数{relation}（{baseline_count} → {patched_count}）。"
        "这支持定位未命中漏洞路径，但仍需人工审查补丁语义才能断言为确定的函数定位错误。",
        baseline_count,
        patched_count,
    )


def manual_function_classification(method: str, target_id: str) -> tuple[str, str]:
    """基于原仓库 PoC 源码、继承关系和补丁 hunk 的人工函数路径复核。"""
    unrelated: dict[tuple[str, str], str] = {
        (
            "agentless",
            "CODEC-270_DBlog-master",
        ): "PoC 只调用 blog-core 的 PasswordUtil.encrypt/decrypt；补丁改的是 blog-admin 的 CredentialsMatcher，测试路径不会实例化该类。",
        (
            "agentless",
            "CVE-2017-7957_rpki-commons",
        ): "PoC 直接构造 ParentIdentitySerializer 并调用 deserialize；补丁改 ProvisioningCmsObjectParser，二者不在该调用链。",
        (
            "agentless",
            "CVE-2020-13956_wechat-ssm",
        ): "PoC 直接调用 HttpUtils 的静态 HTTP 方法；补丁仅改 WeixinAuthController.calback，PoC 不经过控制器。",
        (
            "agentless",
            "CVE-2021-23900_OmegaTester",
        ): "PoC 直接调用 HarConverter.toMyRequest；补丁仅改 ReqCtrl.importRequest，PoC 不经过 Web 控制器。",
        (
            "agentless",
            "CVE-2021-43859_rpki-commons",
        ): "PoC 直接调用 ParentIdentitySerializer.deserialize；补丁改 ProvisioningCmsObjectParser，属于另一条 provisioning payload 路径。",
        (
            "agentless",
            "CVE-2023-43642_flow",
        ): "PoC 直接构造 SnappyCoder 并调用 wrapOut；补丁改 CompressStreamer，PoC 不会经过该 Streamer。",
        (
            "agentless",
            "IO-611_FastJoin",
        ): "PoC 只构造 soj.util.FileReader；补丁改 TopologyArgs 和 FileWriter，均不在 FileReader 的测试调用路径。",
        (
            "appatch",
            "CVE-2017-7957_rpki-commons",
        ): "PoC 使用 ParentIdentitySerializer 的独立 XStream 初始化；补丁改 XStreamXmlSerializerBuilder，未被该 serializer 构造路径调用。",
        (
            "appatch",
            "CVE-2021-43859_rpki-commons",
        ): "PoC 使用 ParentIdentitySerializer；补丁改 PayloadParser、ProvisioningPayloadXmlSerializer 等 payload 路径，不参与 ParentIdentitySerializer.deserialize。",
        (
            "premm",
            "CVE-2019-10086_bean-query",
        ): "PoC 调用 BeanPropertyMatcher.matches，内部走 DefaultNullValuePropertyValueGetter.getProperty；补丁改 PropertySelector，PoC 未构造或调用该 selector。",
        (
            "reinfix",
            "CVE-2019-10086_bean-query",
        ): "PoC 调用 BeanPropertyMatcher.matches，内部走 DefaultNullValuePropertyValueGetter.getProperty；补丁改 PropertySelector，PoC 未构造或调用该 selector。",
        (
            "san2patch",
            "CVE-2019-10086_bean-query",
        ): "PoC 调用 BeanPropertyMatcher.matches，内部走 DefaultNullValuePropertyValueGetter.getProperty；补丁改 PropertySelector，PoC 未构造或调用该 selector。",
        (
            "premm",
            "CVE-2020-13956_crawler-jsoup-maven",
        ): "PoC 调用 CSDNLoginApater.getText/getRedirectLocation/setCookieStore；补丁只修改 main 中的登录流程，不会影响这些被测方法。",
        (
            "reinfix",
            "CVE-2020-13956_crawler-jsoup-maven",
        ): "PoC 调用 CSDNLoginApater.getText/getRedirectLocation/setCookieStore；补丁只修改 main 中的登录流程，不会影响这些被测方法。",
        (
            "sweagent",
            "CVE-2022-29631_ucloud-java-sdk",
        ): "PoC 调用 UFile.getFile，后者使用 HttpRequestUtil；补丁只新增 SafeHttpRequestBuilder，原仓库没有调用该新类。",
    }
    key = (method, target_id)
    if key in unrelated:
        return "真正定位到无关函数", unrelated[key]

    related_evidence = {
        "CODEC-263_DBlog-master": "PoC 直接调用 PasswordUtil；补丁也修改 PasswordUtil，属于被测函数。",
        "CODEC-270_BurpCrypto-master": "PoC 直接调用 AesUtil；补丁也修改 AesUtil，属于被测函数。",
        "CODEC-270_DBlog-master": "PoC 直接调用 PasswordUtil；此补丁修改 PasswordUtil，属于被测函数。",
        "CVE-2015-2156_webbit": "PoC 直接测试 HttpRequestWrapper 的 Cookie 行为；补丁也修改 HttpRequestWrapper。",
        "CVE-2018-1002201_elasticsearch-maven-plugin": "PoC 通过反射调用 ResolveElasticsearchStep；补丁也修改该类。",
        "CVE-2019-10086_bean-query": "PoC 直接调用 BeanPropertyMatcher.matches；此补丁修改 BeanPropertyMatcher。",
        "CVE-2020-13956_wechat-ssm": "PoC 直接调用 HttpUtils 的静态 HTTP 方法；此补丁修改 HttpUtils。",
        "CVE-2021-23899_OmegaTester": "PoC 直接调用 HarConverter.toMyRequest；补丁也修改该方法。",
        "CVE-2021-23900_OmegaTester": "PoC 直接调用 HarConverter.toMyRequest；补丁也修改该方法。",
        "CVE-2021-43859_rpki-commons": "PoC 的 ParentIdentitySerializer 继承 IdentitySerializer；此补丁修改父类的 XStream 初始化链。",
        "CVE-2022-29631_ucloud-java-sdk": "PoC 调用 UFile.getFile，后者调用 HttpRequestUtil；此补丁修改该下游 HTTP 请求构造路径。",
    }
    if target_id not in related_evidence:
        raise ValueError(f"未给出人工函数路径结论：{method}/{target_id}")
    return "定位到PoC相关函数", related_evidence[target_id]


def paths(value: str) -> list[str]:
    return value.split(" | ") if value else []


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- `{item}`" for item in items] or ["- （未解析到路径）"]


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
        method = row["方法"]
        patch_name = row["补丁文件"]
        target_id = patch_name.removesuffix(".patch")
        baseline, patched = summaries[method]
        conclusion, reason, baseline_count, patched_count = report_status(
            baseline.get(target_id), patched.get(target_id)
        )
        manual_conclusion, manual_evidence = manual_function_classification(method, target_id)
        generated_patch = ROOT / "正则化的补丁" / runs[method]["patch_directory"] / patch_name
        baseline_patch = BASELINE_PATCH_ROOT / patch_name
        report_name = f"{method}__{target_id}.md"
        report_path = OUTPUT_DIR / report_name
        baseline_item = baseline.get(target_id)
        patched_item = patched.get(target_id)
        lines = [
            f"# {target_id} / {method}",
            "",
            "## 结论",
            "",
            f"**{conclusion}**",
            "",
            reason,
            "",
            "## 原仓库 PoC 函数路径人工复核",
            "",
            f"**{manual_conclusion}**",
            "",
            manual_evidence,
            "",
            "## 文件定位对比",
            "",
            f"- 生成补丁：`{generated_patch}`",
            f"- baseline 补丁：`{baseline_patch}`",
            "",
            "生成补丁修改文件：",
            *bullet_lines(paths(row["生成补丁修改文件"])),
            "",
            "baseline 修改文件：",
            *bullet_lines(paths(row["baseline 修改文件"])),
            "",
            "## 真实仓库 PoC 验证",
            "",
            f"- 检测模式：`{baseline_item['mode'] if baseline_item else '无'}`",
            f"- baseline 状态：`{baseline_item['status'] if baseline_item else '无'}`",
            f"- 补丁后状态：`{patched_item['status'] if patched_item else '无'}`",
            f"- baseline 漏洞匹配数：`{baseline_count if baseline_count is not None else '不可比较'}`",
            f"- 补丁后漏洞匹配数：`{patched_count if patched_count is not None else '不可比较'}`",
            "",
        ]
        report_path.write_text("\n".join(lines), encoding="utf-8")
        overview.append(
            {
                "方法": method,
                "target_id": target_id,
                "原仓库函数路径结论": manual_conclusion,
                "人工复核依据": manual_evidence,
                "结论": conclusion,
                "baseline漏洞匹配数": baseline_count if baseline_count is not None else "",
                "补丁后漏洞匹配数": patched_count if patched_count is not None else "",
                "逐条报告": report_name,
            }
        )

    overview_path = OUTPUT_DIR / "汇总.csv"
    with overview_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(overview[0]))
        writer.writeheader()
        writer.writerows(overview)
    counts = Counter(str(item["结论"]) for item in overview)
    (OUTPUT_DIR / "README.md").write_text(
        "# 真实仓库 PoC 定位复核\n\n"
        "本目录对 50 个与 baseline 修改文件无交集的补丁实例逐条复核。\n\n"
        f"- 原仓库 PoC 函数路径确认无关：{sum(item['原仓库函数路径结论'] == '真正定位到无关函数' for item in overview)}\n"
        f"- 原仓库 PoC 函数路径相关：{sum(item['原仓库函数路径结论'] == '定位到PoC相关函数' for item in overview)}\n\n"
        f"- PoC 支持疑似函数定位错误：{counts['PoC支持疑似函数定位错误']}\n"
        f"- PoC 验证有效（非定位错误）：{counts['PoC验证有效（非定位错误）']}\n"
        f"- 未验证（编译/执行异常或不可比较）：{counts['未验证']}\n\n"
        "原仓库函数路径结论以 PoC 实际调用的类/方法、继承关系和补丁 hunk 为准；PoC 运行计数仅作为辅助证据。\n",
        encoding="utf-8",
    )
    print(f"已生成 {len(overview)} 份逐条报告：{OUTPUT_DIR}")
    print(dict(counts))


if __name__ == "__main__":
    main()
