# CODEC-270_DBlog-master / premm

## 原仓库 PoC 入口

- Dtest：`PasswordUtil_ESTest`
- PoC 源码：`/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/CODEC-270_DBlog-master/blog-core/evosuite-tests/com/zyd/blog/util/PasswordUtil_ESTest.java

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_premm_20260701_193017/CODEC-270_DBlog-master.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_DBlog-master.patch`

生成补丁修改文件：
- `blog-core/src/main/java/com/zyd/blog/util/PasswordUtil.java`

baseline 修改文件：
- `blog-admin/src/main/java/com/zyd/blog/core/websocket/util/WebSocketUtil.java`
- `blog-core/src/main/java/com/zyd/blog/util/AesUtil.java`

## 真实仓库 PoC 运行结果

- 运行判定：**未验证：补丁编译/执行异常**
- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`COMPILE_FAILED`
- baseline 漏洞匹配数：`不可比较`
- 补丁后漏洞匹配数：`不可比较`

## 原仓库函数路径人工结论

**定位到 PoC 相关函数/调用链**

依据：PoC 直接调用 `PasswordUtil.encrypt/decrypt`；补丁 hunk 位于 `PasswordUtil`。
