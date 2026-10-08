# CODEC-270_BurpCrypto-master / san2patch

## Conclusion

**PoC verification effective (not a localization error)**

Although the files modified differ from the baseline, the real-repository PoC vulnerability match count did decrease, so the patch still hits the relevant code path.

## Manual review of the original-repository PoC function path

**Localized to a PoC-related function**

The PoC calls AesUtil directly; the patch also modifies AesUtil, which is the function under test.

## File-localization comparison

- Generated patch: `/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁/normalized_patches_san2patch_20260724_170854/CODEC-270_BurpCrypto-master.patch`
- Baseline patch: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_BurpCrypto-master.patch`

Files modified by the generated patch:
- `src/main/java/burp/aes/AesUtil.java`

Files modified by the baseline:
- `src/main/java/burp/utils/Utils.java`

## Real-repository PoC verification

- Detection mode: `poc_string`
- Baseline status: `VULNERABLE`
- Post-patch status: `NOT_VULNERABLE`
- Baseline vulnerability match count: `4`
- Post-patch vulnerability match count: `0`
