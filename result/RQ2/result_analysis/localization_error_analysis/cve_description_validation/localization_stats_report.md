# Normalized-patch localization statistics

## Statistical conclusion

- Total normalized patches: 460
- Localization correct: 386 (83.91%)
- Localization problem: 74 method-patch instances (16.09%)
- Patch files with a localization problem: 29 (de-duplicated by patch name across methods)

## Decision criteria

The corresponding baseline patch is looked up by patch filename, and the repository-relative file paths modified by each of the two patches are extracted separately. As soon as the two share at least one identical file path, the localization is judged correct; with no overlap it is judged problematic. The `a/` and `b/` prefixes are stripped before comparing.

- Normalized-patch directory: `/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁`
- Baseline directory: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline`
- Missing same-named baseline: 0
- Generated patch yielded no file path: 0
- Baseline yielded no file path: 0

## Per-method summary

| method | patch_total | localization_correct | localization_problem | correct_rate | error_rate |
|---|---:|---:|---:|---:|---:|
| agentless | 57 | 46 | 11 | 80.70% | 19.30% |
| appatch | 49 | 40 | 9 | 81.63% | 18.37% |
| openhands | 62 | 58 | 4 | 93.55% | 6.45% |
| patchagent | 40 | 34 | 6 | 85.00% | 15.00% |
| premm | 49 | 38 | 11 | 77.55% | 22.45% |
| reinfix | 63 | 52 | 11 | 82.54% | 17.46% |
| repairagent | 40 | 30 | 10 | 75.00% | 25.00% |
| san2patch | 41 | 31 | 10 | 75.61% | 24.39% |
| sweagent | 59 | 57 | 2 | 96.61% | 3.39% |
| **Total** | **460** | **386** | **74** | **83.91%** | **16.09%** |

## De-duplicated failing patches

| patch_file | localization_error_method_count | localization_error_methods |
|---|---:|---|
| CODEC-263_DBlog-master.patch | 3 | premm, reinfix, san2patch |
| CODEC-270_BurpCrypto-master.patch | 3 | premm, reinfix, san2patch |
| CODEC-270_DBlog-master.patch | 4 | agentless, premm, reinfix, san2patch |
| CVE-2015-2156_webbit.patch | 6 | agentless, openhands, patchagent, premm, reinfix, san2patch |
| CVE-2017-7957_rpki-commons.patch | 2 | appatch, repairagent |
| CVE-2018-1002201_elasticsearch-maven-plugin.patch | 4 | patchagent, premm, reinfix, san2patch |
| CVE-2018-15756_mirage.patch | 3 | agentless, openhands, patchagent |
| CVE-2019-10086_bean-query.patch | 4 | premm, reinfix, repairagent, san2patch |
| CVE-2019-12415_poi-examples.patch | 1 | appatch |
| CVE-2020-13956_crawler-jsoup-maven.patch | 3 | premm, reinfix, repairagent |
| CVE-2020-13956_wechat-ssm.patch | 7 | agentless, appatch, openhands, premm, reinfix, san2patch, sweagent |
| CVE-2021-23899_OmegaTester.patch | 4 | agentless, premm, reinfix, san2patch |
| CVE-2021-23900_OmegaTester.patch | 3 | premm, reinfix, san2patch |
| CVE-2021-35516_JavaUtils-master.patch | 1 | repairagent |
| CVE-2021-43859_rpki-commons.patch | 6 | agentless, appatch, openhands, patchagent, repairagent, sweagent |
| CVE-2022-22976_RuoYi-Vue-Multi-Tenant.patch | 1 | repairagent |
| CVE-2022-22976_gerenciador-viagens.patch | 2 | agentless, repairagent |
| CVE-2022-25845_base-starter.patch | 1 | appatch |
| CVE-2022-25845_geek_framework.patch | 2 | appatch, repairagent |
| CVE-2022-29631_ucloud-java-sdk.patch | 4 | appatch, premm, reinfix, san2patch |
| CVE-2022-42889_java.patch | 1 | agentless |
| CVE-2022-45688_virtress.patch | 2 | patchagent, repairagent |
| CVE-2023-1370_microservice-with-jwt-and-microprofile.patch | 1 | patchagent |
| CVE-2023-34453_UltraPlaytime.patch | 1 | agentless |
| IO-611_FastJoin.patch | 1 | repairagent |
| IO-611_velocity-engine.patch | 1 | appatch |
| LANG-1385_ewallet.patch | 1 | appatch |
| LANG-1385_wechat-ssm.patch | 1 | agentless |
| LANG-1484_jjdz7-drony-refactor.patch | 1 | agentless |

All 74 error instances and the modified file paths on both sides are in `localization_errors_detail.csv`; the results de-duplicated by patch are in `localization_errors_by_patch.csv`.