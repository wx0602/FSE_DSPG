# IO-611_velocity-engine / appatch

## 原仓库 PoC 入口

- Dtest：`FileResourceLoader_ESTest`
- PoC 源码：`/media/wql/办公/AVR_agent/downstream_dataset/resource_20260816/IO-611_velocity-engine/velocity-engine-core/evosuite-tests/org/apache/velocity/runtime/resource/loader/FileResourceLoader_ESTest.java

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/CVE 描述验证结果/正则化的补丁/normalized_patches_appatch_20260701_193006/IO-611_velocity-engine.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/IO-611_velocity-engine.patch`

生成补丁修改文件：
- `velocity-engine-core/src/main/java/org/apache/velocity/app/event/EventHandlerUtil.java`

baseline 修改文件：
- `velocity-engine-core/src/main/java/org/apache/velocity/runtime/resource/loader/FileResourceLoader.java`

## 真实仓库 PoC 运行结果

- 运行判定：**PoC匹配数未降低**
- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`VULNERABLE`
- baseline 漏洞匹配数：`4`
- 补丁后漏洞匹配数：`4`

## 原仓库函数路径人工结论

**真正定位到无关函数**

依据：PoC 直接调用 `FileResourceLoader`；补丁改 `EventHandlerUtil`，不在资源加载路径。
