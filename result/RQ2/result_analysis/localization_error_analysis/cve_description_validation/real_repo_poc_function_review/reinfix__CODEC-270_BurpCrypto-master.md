# CODEC-270_BurpCrypto-master / reinfix

## Original-repository PoC entry point

- Dtest: `AesUtil_ESTest`
- PoC source: `/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/CODEC-270_BurpCrypto-master/evosuite-tests/burp/aes/AesUtil_ESTest.java

## File-localization comparison

- Generated patch: `/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_reinfix_20260701_193019/CODEC-270_BurpCrypto-master.patch`
- Baseline patch: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_BurpCrypto-master.patch`

Files modified by the generated patch:
- `src/main/java/burp/aes/AesUtil.java`

Files modified by the baseline:
- `src/main/java/burp/utils/Utils.java`

## Real-repository PoC run result

- Run verdict: **PoC match count increased**
- Detection mode: `poc_string`
- Baseline status: `VULNERABLE`
- Post-patch status: `VULNERABLE`
- Baseline vulnerability match count: `4`
- Post-patch vulnerability match count: `8`

## Manual conclusion on the original-repository function path

**Localized to a PoC-related function / call chain**

Basis: The PoC constructs and calls `AesUtil.encrypt/decrypt` directly; the patch hunk is located in `AesUtil`.
