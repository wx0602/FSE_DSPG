# 三组修复失败、组合组修复成功的 case

## 结论

严格口径下共找到 **9 个 `<工具, 补丁>` 对**。

严格判定条件：

- `带漏洞链验证结果_矩阵.csv == 修复失败`
- `CVE 描述验证结果_矩阵.csv == 修复失败`
- `带自生成上游补丁验证结果_矩阵.csv == 修复失败`
- `带自生成上游补丁加漏洞链验证结果_矩阵.csv == success`

四张矩阵均有 567 个相同的 `target_id × 工具` 键（63 个 target、9 个工具），因此不存在因缺行或缺工具造成的漏配。

## 所有严格口径 case

1. `patchagent` × `CODEC-263_DBlog-master.patch`
2. `repairagent` × `CODEC-263_DBlog-master.patch`
3. `repairagent` × `CVE-2017-7957_cqrs-lottery-master.patch`
4. `premm` × `CVE-2021-23899_json-sanitizer.patch`
5. `sweagent` × `CVE-2021-39144_source.patch`
6. `openhands` × `CVE-2021-43859_rpki-commons.patch`
7. `repairagent` × `CVE-2022-25845_geek_framework.patch`
8. `repairagent` × `CVE-2022-29631_ucloud-java-sdk.patch`
9. `repairagent` × `CVE-2022-45688_virtress.patch`

按工具统计：openhands 1 对、patchagent 1 对、premm 1 对、repairagent 5 对、sweagent 1 对。

详细的四组状态、成功补丁路径、SHA-256 和文件大小见 `所有case_严格口径.csv`；对应成功补丁已复制到 `成功补丁/`。

## 宽口径附录

如果把 `编译错误` 和 `empty` 也算作“没有修复成功”，则共 35 对。完整清单见 `附录_前三组均未success.csv`，其中用“是否也属于严格口径”标出了上述 9 对。

## 数据来源与复现

- `漏洞链`：`带漏洞链验证结果_矩阵.csv`
- `CVE描述`：`CVE 描述验证结果_矩阵.csv`
- `自生成上游补丁`：`带自生成上游补丁验证结果_矩阵.csv`
- `自生成上游补丁加漏洞链`：`带自生成上游补丁加漏洞链验证结果_矩阵.csv`

组合实验采用最新的完整批次：`带自生成上游补丁加漏洞链验证结果/nine_patch_validation_20260830_202357/pipeline_summary.json`。

在本目录执行 `python3 生成结果.py` 可重新计算清单并刷新补丁副本。脚本会校验四张矩阵的工具列和全部键完全一致。
