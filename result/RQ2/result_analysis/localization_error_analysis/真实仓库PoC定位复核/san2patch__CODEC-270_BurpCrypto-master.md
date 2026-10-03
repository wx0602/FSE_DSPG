# CODEC-270_BurpCrypto-master / san2patch

## 结论

**PoC验证有效（非定位错误）**

虽然修改文件与 baseline 不同，但真实仓库 PoC 的漏洞匹配数已降低，补丁仍命中了相关代码路径。

## 原仓库 PoC 函数路径人工复核

**定位到PoC相关函数**

PoC 直接调用 AesUtil；补丁也修改 AesUtil，属于被测函数。

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁/normalized_patches_san2patch_20260724_170854/CODEC-270_BurpCrypto-master.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/CODEC-270_BurpCrypto-master.patch`

生成补丁修改文件：
- `src/main/java/burp/aes/AesUtil.java`

baseline 修改文件：
- `src/main/java/burp/utils/Utils.java`

## 真实仓库 PoC 验证

- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`NOT_VULNERABLE`
- baseline 漏洞匹配数：`4`
- 补丁后漏洞匹配数：`0`
