# CODEC-263_DBlog-master / premm

## 结论

**未验证**

补丁编译或执行异常，不能据此判断函数定位。

## 原仓库 PoC 函数路径人工复核

**定位到PoC相关函数**

PoC 直接调用 PasswordUtil；补丁也修改 PasswordUtil，属于被测函数。

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁/normalized_patches_premm_20260724_170850/CODEC-263_DBlog-master.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-263_DBlog-master.patch`

生成补丁修改文件：
- `blog-core/src/main/java/com/zyd/blog/util/PasswordUtil.java`

baseline 修改文件：
- `blog-admin/src/main/java/com/zyd/blog/core/websocket/util/WebSocketUtil.java`
- `blog-core/src/main/java/com/zyd/blog/util/AesUtil.java`

## 真实仓库 PoC 验证

- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`COMPILE_FAILED`
- baseline 漏洞匹配数：`不可比较`
- 补丁后漏洞匹配数：`不可比较`
