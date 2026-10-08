# CODEC-270_DBlog-master / san2patch

## Original-repository PoC entry point

- Dtest: `PasswordUtil_ESTest`
- PoC source: `/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/CODEC-270_DBlog-master/blog-core/evosuite-tests/com/zyd/blog/util/PasswordUtil_ESTest.java

## File-localization comparison

- Generated patch: `/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_san2patch_20260701_193021/CODEC-270_DBlog-master.patch`
- Baseline patch: `/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_DBlog-master.patch`

Files modified by the generated patch:
- `blog-core/src/main/java/com/zyd/blog/util/PasswordUtil.java`

Files modified by the baseline:
- `blog-admin/src/main/java/com/zyd/blog/core/websocket/util/WebSocketUtil.java`
- `blog-core/src/main/java/com/zyd/blog/util/AesUtil.java`

## Real-repository PoC run result

- Run verdict: **PoC match count decreased**
- Detection mode: `poc_string`
- Baseline status: `VULNERABLE`
- Post-patch status: `NOT_VULNERABLE`
- Baseline vulnerability match count: `3`
- Post-patch vulnerability match count: `0`

## Manual conclusion on the original-repository function path

**Localized to a PoC-related function / call chain**

Basis: The PoC calls `PasswordUtil.encrypt/decrypt` directly; the patch hunk is located in `PasswordUtil`.
