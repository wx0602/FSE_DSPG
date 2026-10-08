# Normalized-patch localization statistics

## Statistical conclusion

- Total normalized patches: 503
- Localization correct: 453 (90.06%)
- Localization problem: 50 method-patch instances (9.94%)
- Patch files with a localization problem: 15 (de-duplicated by patch name across methods)

## Decision criteria

The corresponding baseline patch is looked up by patch filename, and the repository-relative file paths modified by each of the two patches are extracted separately. As soon as the two share at least one identical file path, the localization is judged correct; with no overlap it is judged problematic. The `a/` and `b/` prefixes are stripped before comparing.

- Normalized-patch directory: `/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁`
- Baseline directory: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline`
- Missing same-named baseline: 0
- Generated patch yielded no file path: 0
- Baseline yielded no file path: 0

## Per-method summary

| method | patch_total | localization_correct | localization_problem | correct_rate | error_rate |
|---|---:|---:|---:|---:|---:|
| agentless | 54 | 46 | 8 | 85.19% | 14.81% |
| appatch | 63 | 60 | 3 | 95.24% | 4.76% |
| openhands | 62 | 61 | 1 | 98.39% | 1.61% |
| patchagent | 60 | 58 | 2 | 96.67% | 3.33% |
| premm | 48 | 37 | 11 | 77.08% | 22.92% |
| reinfix | 63 | 52 | 11 | 82.54% | 17.46% |
| repairagent | 53 | 52 | 1 | 98.11% | 1.89% |
| san2patch | 43 | 33 | 10 | 76.74% | 23.26% |
| sweagent | 57 | 54 | 3 | 94.74% | 5.26% |
| **Total** | **503** | **453** | **50** | **90.06%** | **9.94%** |

## De-duplicated failing patches

| patch_file | localization_error_method_count | localization_error_methods |
|---|---:|---|
| CODEC-263_DBlog-master.patch | 3 | premm, reinfix, san2patch |
| CODEC-270_BurpCrypto-master.patch | 3 | premm, reinfix, san2patch |
| CODEC-270_DBlog-master.patch | 4 | agentless, premm, reinfix, san2patch |
| CVE-2015-2156_webbit.patch | 3 | premm, reinfix, san2patch |
| CVE-2017-7957_rpki-commons.patch | 2 | agentless, appatch |
| CVE-2018-1002201_elasticsearch-maven-plugin.patch | 3 | premm, reinfix, san2patch |
| CVE-2019-10086_bean-query.patch | 4 | agentless, premm, reinfix, san2patch |
| CVE-2020-13956_crawler-jsoup-maven.patch | 2 | premm, reinfix |
| CVE-2020-13956_wechat-ssm.patch | 8 | agentless, appatch, openhands, patchagent, premm, reinfix, san2patch, sweagent |
| CVE-2021-23899_OmegaTester.patch | 3 | premm, reinfix, san2patch |
| CVE-2021-23900_OmegaTester.patch | 4 | agentless, premm, reinfix, san2patch |
| CVE-2021-43859_rpki-commons.patch | 5 | agentless, appatch, patchagent, repairagent, sweagent |
| CVE-2022-29631_ucloud-java-sdk.patch | 4 | premm, reinfix, san2patch, sweagent |
| CVE-2023-43642_flow.patch | 1 | agentless |
| IO-611_FastJoin.patch | 1 | agentless |

All 50 error instances and the modified file paths on both sides are in `localization_errors_detail.csv`; the results de-duplicated by patch are in `localization_errors_by_patch.csv`.