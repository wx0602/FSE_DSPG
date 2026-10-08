# LANG-1385_ewallet / appatch

## Original-repository PoC entry point

- Dtest: `NumberUtil_ESTest`
- PoC source: `/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/LANG-1385_ewallet/wallet-base/evosuite-tests/com/fr/chain/utils/NumberUtil_ESTest.java

## File-localization comparison

- Generated patch: `/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_appatch_20260701_193006/LANG-1385_ewallet.patch`
- Baseline patch: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/LANG-1385_ewallet.patch`

Files modified by the generated patch:
- `wallet-base/src/main/java/com/fr/chain/utils/MBUtil.java`
- `wallet-base/src/main/java/com/fr/chain/utils/NumberParser.java`

Files modified by the baseline:
- `wallet-base/src/main/java/com/fr/chain/utils/NumberUtil.java`

## Real-repository PoC run result

- Run verdict: **PoC match count did not decrease**
- Detection mode: `poc_string`
- Baseline status: `VULNERABLE`
- Post-patch status: `VULNERABLE`
- Baseline vulnerability match count: `5`
- Post-patch vulnerability match count: `5`

## Manual conclusion on the original-repository function path

**Genuinely localized to an unrelated function**

Basis: The PoC calls `NumberUtil` directly; the patch changes `MBUtil`/`NumberParser`, with no call relationship.
