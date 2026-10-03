# CODEC-270_DBlog-master / agentless

## 结论

**PoC支持疑似函数定位错误**

修改文件与 baseline 不同，且真实仓库 PoC 的漏洞匹配数相同（3 → 3）。这支持定位未命中漏洞路径，但仍需人工审查补丁语义才能断言为确定的函数定位错误。

## 原仓库 PoC 函数路径人工复核

**真正定位到无关函数**

PoC 只调用 blog-core 的 PasswordUtil.encrypt/decrypt；补丁改的是 blog-admin 的 CredentialsMatcher，测试路径不会实例化该类。

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁/normalized_patches_agentless_20260724_170845/CODEC-270_DBlog-master.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_DBlog-master.patch`

生成补丁修改文件：
- `blog-admin/src/main/java/com/zyd/blog/core/shiro/credentials/CredentialsMatcher.java`

baseline 修改文件：
- `blog-admin/src/main/java/com/zyd/blog/core/websocket/util/WebSocketUtil.java`
- `blog-core/src/main/java/com/zyd/blog/util/AesUtil.java`

## 真实仓库 PoC 验证

- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`VULNERABLE`
- baseline 漏洞匹配数：`3`
- 补丁后漏洞匹配数：`3`
