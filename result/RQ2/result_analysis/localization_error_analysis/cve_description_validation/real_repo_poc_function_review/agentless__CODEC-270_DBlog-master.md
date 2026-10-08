# CODEC-270_DBlog-master / agentless

## Original-repository PoC entry point

- Dtest: `PasswordUtil_ESTest`
- PoC source: `/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/CODEC-270_DBlog-master/blog-core/evosuite-tests/com/zyd/blog/util/PasswordUtil_ESTest.java

## File-localization comparison

- Generated patch: `/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_agentless_20260701_192933/CODEC-270_DBlog-master.patch`
- Baseline patch: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_DBlog-master.patch`

Files modified by the generated patch:
- `blog-admin/src/main/java/com/zyd/blog/core/config/ShiroConfig.java`

Files modified by the baseline:
- `blog-admin/src/main/java/com/zyd/blog/core/websocket/util/WebSocketUtil.java`
- `blog-core/src/main/java/com/zyd/blog/util/AesUtil.java`

## Real-repository PoC run result

- Run verdict: **PoC match count did not decrease**
- Detection mode: `poc_string`
- Baseline status: `VULNERABLE`
- Post-patch status: `VULNERABLE`
- Baseline vulnerability match count: `3`
- Post-patch vulnerability match count: `3`

## Manual conclusion on the original-repository function path

**Genuinely localized to an unrelated function**

Basis: The PoC only calls `blog-core/PasswordUtil.encrypt/decrypt`; the patch changes the rememberMe cookie configuration in `blog-admin/ShiroConfig`, with no call relationship.
