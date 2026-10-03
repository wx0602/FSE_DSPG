# CODEC-270_BurpCrypto-master / reinfix

## 原仓库 PoC 入口

- Dtest：`AesUtil_ESTest`
- PoC 源码：`/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/CODEC-270_BurpCrypto-master/evosuite-tests/burp/aes/AesUtil_ESTest.java

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_reinfix_20260701_193019/CODEC-270_BurpCrypto-master.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_BurpCrypto-master.patch`

生成补丁修改文件：
- `src/main/java/burp/aes/AesUtil.java`

baseline 修改文件：
- `src/main/java/burp/utils/Utils.java`

## 真实仓库 PoC 运行结果

- 运行判定：**PoC匹配数升高**
- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`VULNERABLE`
- baseline 漏洞匹配数：`4`
- 补丁后漏洞匹配数：`8`

## 原仓库函数路径人工结论

**定位到 PoC 相关函数/调用链**

依据：PoC 直接构造并调用 `AesUtil.encrypt/decrypt`；补丁 hunk 位于 `AesUtil`。
