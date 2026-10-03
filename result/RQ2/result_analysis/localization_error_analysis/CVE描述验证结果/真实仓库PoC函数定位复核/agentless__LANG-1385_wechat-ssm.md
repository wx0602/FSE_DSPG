# LANG-1385_wechat-ssm / agentless

## 原仓库 PoC 入口

- Dtest：`MyNumberUtils_ESTest`
- PoC 源码：`/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/LANG-1385_wechat-ssm/evosuite-tests/cn/qs/utils/format/MyNumberUtils_ESTest.java

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_agentless_20260701_192933/LANG-1385_wechat-ssm.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/LANG-1385_wechat-ssm.patch`

生成补丁修改文件：
- `src/main/java/cn/qs/exceptionHandler/AjaxExceptionHandler.java`

baseline 修改文件：
- `src/main/java/cn/qs/utils/format/MyNumberUtils.java`

## 真实仓库 PoC 运行结果

- 运行判定：**PoC匹配数未降低**
- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`VULNERABLE`
- baseline 漏洞匹配数：`8`
- 补丁后漏洞匹配数：`8`

## 原仓库函数路径人工结论

**真正定位到无关函数**

依据：PoC 直接调用 `MyNumberUtils`；补丁改 `AjaxExceptionHandler`，无调用关系。
