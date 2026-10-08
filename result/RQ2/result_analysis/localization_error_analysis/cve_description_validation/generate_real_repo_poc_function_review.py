#!/usr/bin/env python3
"""以原仓库 PoC 的实际调用路径复核 CVE 描述组的 74 个定位错误实例。

“无关函数”只指补丁 hunk 没有落在 PoC 直接调用的函数、其调用链或继承链上；
不以 PoC 输出中的漏洞字符串数量作为定位结论。
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "real_repo_poc_function_review"

# 经逐项查看 PoC 源码、目标类和补丁 hunk 后，仍位于 PoC 函数/调用链的实例。
RELATED = {
    "agentless__CVE-2020-13956_wechat-ssm",
    "appatch__CVE-2020-13956_wechat-ssm",
    "appatch__CVE-2022-29631_ucloud-java-sdk",
    "openhands__CVE-2020-13956_wechat-ssm",
    "openhands__CVE-2021-43859_rpki-commons",
    "sweagent__CVE-2020-13956_wechat-ssm",
    "sweagent__CVE-2021-43859_rpki-commons",
    *{f"{method}__{target}" for method in ("premm", "reinfix", "san2patch") for target in (
        "CODEC-263_DBlog-master",
        "CODEC-270_BurpCrypto-master",
        "CODEC-270_DBlog-master",
        "CVE-2015-2156_webbit",
        "CVE-2018-1002201_elasticsearch-maven-plugin",
        "CVE-2020-13956_wechat-ssm",
        "CVE-2021-23899_OmegaTester",
        "CVE-2021-23900_OmegaTester",
        "CVE-2022-29631_ucloud-java-sdk",
    )},
}

RELATED_EVIDENCE = {
    "CODEC-263_DBlog-master": "PoC 直接调用 `PasswordUtil.encrypt/decrypt`；补丁 hunk 位于 `PasswordUtil`。",
    "CODEC-270_BurpCrypto-master": "PoC 直接构造并调用 `AesUtil.encrypt/decrypt`；补丁 hunk 位于 `AesUtil`。",
    "CODEC-270_DBlog-master": "PoC 直接调用 `PasswordUtil.encrypt/decrypt`；补丁 hunk 位于 `PasswordUtil`。",
    "CVE-2015-2156_webbit": "PoC 调用 `HttpRequestWrapper.cookies()`；补丁 hunk 正是该委托方法（即使实际解析由 `StubHttpRequest/InboundCookieParser` 完成）。",
    "CVE-2018-1002201_elasticsearch-maven-plugin": "PoC 通过反射直接调用 `ResolveElasticsearchStep.unpackToElasticsearchDirectory`；补丁 hunk 位于该类。",
    "CVE-2020-13956_wechat-ssm": "PoC 直接调用 `HttpUtils.doGet/doPost` 等；补丁 hunk 改写这些请求方法的 URI 构造。",
    "CVE-2021-23899_OmegaTester": "PoC 构造 `HarConverter` 并调用 `toMyRequest`；补丁 hunk 位于该输入转换链。",
    "CVE-2021-23900_OmegaTester": "PoC 直接调用 `HarConverter.toMyRequest`；补丁 hunk 位于该类的嵌套 JSON 处理路径。",
    "CVE-2021-43859_rpki-commons": "PoC 调用 `ParentIdentitySerializer.deserialize`；该类继承 `IdentitySerializer`，补丁 hunk 修改其构造阶段创建的 XStream。",
    "CVE-2022-29631_ucloud-java-sdk": "PoC 调用 `UFile.getFile`，其请求发送链会进入 `HttpRequestUtil`；补丁 hunk 位于这条下游请求链。",
}

UNRELATED_EVIDENCE = {
    "CODEC-270_DBlog-master": "PoC 只调用 `blog-core/PasswordUtil.encrypt/decrypt`；补丁改 `blog-admin/ShiroConfig` 的 rememberMe Cookie 配置，无调用关系。",
    "CVE-2015-2156_webbit": "PoC 路径为 `HttpRequestWrapper.cookies() → StubHttpRequest.cookies() → InboundCookieParser.parse()`；补丁改的是响应对象/`CookieHeaderSanitizer`，不在该入站解析链。",
    "CVE-2017-7957_rpki-commons": "PoC 调用 `ParentIdentitySerializer.deserialize`；补丁只改通用 `XStreamXmlSerializerBuilder`，而 ParentIdentitySerializer 自行在父类构造器中创建 XStream。",
    "CVE-2018-1002201_elasticsearch-maven-plugin": "PoC 反射调用 `ResolveElasticsearchStep.unpackToElasticsearchDirectory`；补丁改 `InstallPluginsStep`/`FilesystemUtil`，未进入该私有解压函数。",
    "CVE-2018-15756_mirage": "PoC 直接调用 `ResponseDelegate.getResp().file(...)`；补丁改启动类或 DSL 拦截/映射类，不在 ResponseDelegate 文件响应路径。",
    "CVE-2019-10086_bean-query": "PoC 仅经 `BeanPropertyMatcher.matches → DefaultNullValuePropertyValueGetter.getProperty` 解析 `class`；补丁改 `PropertySelector` 或 `ClassSelector`，两者未被调用。",
    "CVE-2019-12415_poi-examples": "PoC 直接调用 `CustomXMLMapping.main`；补丁改 `XLSX2CSV`，无调用关系。",
    "CVE-2020-13956_crawler-jsoup-maven": "PoC 调用 `CSDNLoginApater.getText/getRedirectLocation/setCookieStore`；补丁只改 `CSDNLoginApater.main` 或无关的 `GrabUnits`，未触及这些方法。",
    "CVE-2021-23899_OmegaTester": "PoC 直接调用 `JsonSanitizer.sanitize` 与 `HarConverter.toMyRequest`；补丁只改 `JavaExecScript`，不在这两条路径。",
    "CVE-2021-35516_JavaUtils-master": "PoC 直接调用 `ZipPwdUtil`；补丁改独立的 `AESUtil`，无调用关系。",
    "CVE-2021-43859_rpki-commons": "PoC 使用 `ParentIdentitySerializer`（其父类为 `IdentitySerializer`）；补丁只改 `XStreamXmlSerializer` 或其 Builder，未被该 serializer 构造/deserialize 路径使用。",
    "CVE-2022-22976_RuoYi-Vue-Multi-Tenant": "PoC 直接调用 `SecurityUtils.matchesPassword`；补丁改 Web 安全配置 `SecurityConfig`，PoC 不启动该配置链。",
    "CVE-2022-22976_gerenciador-viagens": "PoC 直接调用 `SenhaUtils.senhaValida`；补丁改 `WebSecurityConfig` 的 PasswordEncoder Bean，测试路径未加载该 Bean。",
    "CVE-2022-25845_base-starter": "PoC 直接调用 `RequestUtils.readData`；补丁改 Spring 的 `FastjsonSafeModeConfiguration`，不在该直接解析调用链。",
    "CVE-2022-25845_geek_framework": "PoC 直接调用 `JsonUtil.parse`；补丁改应用启动类 `Application`，测试不经过启动流程。",
    "CVE-2022-42889_java": "PoC 直接调用 `SearchController.search`；补丁改 `App`，未进入控制器搜索路径。",
    "CVE-2022-45688_virtress": "PoC 直接调用 `Converter.xmlToJson`；补丁改 `App`，无调用关系。",
    "CVE-2023-1370_microservice-with-jwt-and-microprofile": "PoC 直接调用 `TokenUtil.generateTokenString`；补丁改 `MoviesResource`，不在 TokenUtil 路径。",
    "CVE-2023-34453_UltraPlaytime": "PoC 直接构造并调用 `RewardsUtils`；补丁改插件主类及依赖下载管理类，未进入 RewardsUtils。",
    "IO-611_FastJoin": "PoC 仅构造/使用 `FileReader`；补丁改 `FileWriter`，无调用关系。",
    "IO-611_velocity-engine": "PoC 直接调用 `FileResourceLoader`；补丁改 `EventHandlerUtil`，不在资源加载路径。",
    "LANG-1385_ewallet": "PoC 直接调用 `NumberUtil`；补丁改 `MBUtil`/`NumberParser`，无调用关系。",
    "LANG-1385_wechat-ssm": "PoC 直接调用 `MyNumberUtils`；补丁改 `AjaxExceptionHandler`，无调用关系。",
    "LANG-1484_jjdz7-drony-refactor": "PoC 直接调用 `Validator`；补丁改 `IoTools`，无调用关系。",
}


def conclusion(key: str, target: str) -> tuple[str, str]:
    if key in RELATED:
        return 'localized_to_poc_related_function_or_call_chain'call_chain'arget]
    return 'localized_to_unrelated_function'ion'CE[target]


def main() -> None:
    summary = ROOT / "summary.csv"
    with summary.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    reviewed = []
    for row in rows:
        key = f"{row['method'{row['target_id']}"
        label, evidence = conclusion(key, row["target_id"])
        row['original_repo_function_path_conclusion'conclusion'row['manual_review_basis''
        reviewed.append(row)

        report = ROOT / row['per_case_report'rt'  text = report.read_text(encoding="utf-8")
        replacement = (
            "## 原仓库函数路径人工结论\n\n"
            f"**{label}**\n\n"
            f"依据：{evidence}\n"
        )
        text = re.sub(
            r"## 原仓库函数路径人工结论\n\n[\s\S]*$", replacement, text
        )
        report.write_text(text, encoding="utf-8")

    fields = list(reviewed[0])
    with summary.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reviewed)

    unrelated = [r for r in reviewed if r['original_repo_function_path_conclusion'conclusion'    w'localized_to_unrelated_function'ion'elated_function.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(unrelated)

    related = len(reviewed) - len(unrelated)
    (ROOT / "README.md").write_text(
        "# CVE 描述组：真实仓库 PoC 函数定位复核\n\n"
        f"共复核 **{len(reviewed)}** 个文件路径不重合实例：\n\n"
        f"- **{len(unrelated)}** 个真正定位到无关函数；\n"
        f"- **{related}** 个仍在 PoC 的直接调用、下游调用或继承链上，不能算函数定位错误。\n\n"
        "判定只依据原仓库 PoC 源码、调用/继承关系和补丁 hunk；PoC 的漏洞字符串计数仅保留在逐条报告中作为运行现象，不参与函数定位结论。\n\n"
        "- `summary.csv`：全部 74 项及逐项依据。\n"
        "- `localized_to_unrelated_function.csv`：仅真正无关的实例。\n"
        "- `方法__target.md`：每个补丁实例的一份独立报告。\n",
        encoding="utf-8",
    )
    print(f"全部实例: {len(reviewed)}；真正无关: {len(unrelated)}；PoC相关: {related}")


if __name__ == "__main__":
    main()
