# LANG-1385_wechat-ssm / agentless

## Original-repository PoC entry point

- Dtest: `MyNumberUtils_ESTest`
- PoC source: `/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/LANG-1385_wechat-ssm/evosuite-tests/cn/qs/utils/format/MyNumberUtils_ESTest.java

## File-localization comparison

- Generated patch: `/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_agentless_20260701_192933/LANG-1385_wechat-ssm.patch`
- Baseline patch: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/LANG-1385_wechat-ssm.patch`

Files modified by the generated patch:
- `src/main/java/cn/qs/exceptionHandler/AjaxExceptionHandler.java`

Files modified by the baseline:
- `src/main/java/cn/qs/utils/format/MyNumberUtils.java`

## Real-repository PoC run result

- Run verdict: **PoC match count did not decrease**
- Detection mode: `poc_string`
- Baseline status: `VULNERABLE`
- Post-patch status: `VULNERABLE`
- Baseline vulnerability match count: `8`
- Post-patch vulnerability match count: `8`

## Manual conclusion on the original-repository function path

**Genuinely localized to an unrelated function**

Basis: The PoC calls `MyNumberUtils` directly; the patch changes `AjaxExceptionHandler`, with no call relationship.
