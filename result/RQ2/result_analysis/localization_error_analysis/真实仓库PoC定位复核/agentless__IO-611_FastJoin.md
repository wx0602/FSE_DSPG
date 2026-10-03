# IO-611_FastJoin / agentless

## 结论

**未验证**

补丁编译或执行异常，不能据此判断函数定位。

## 原仓库 PoC 函数路径人工复核

**真正定位到无关函数**

PoC 只构造 soj.util.FileReader；补丁改 TopologyArgs 和 FileWriter，均不在 FileReader 的测试调用路径。

## 文件定位对比

- 生成补丁：`/media/wql/办公/AVR_agent/7月实验结果验证/带漏洞链验证结果/正则化的补丁/normalized_patches_agentless_20260724_170845/IO-611_FastJoin.patch`
- baseline 补丁：`/media/wql/办公/AVR_agent/history_patch_agent/vaildate_patch/patch_baseline/IO-611_FastJoin.patch`

生成补丁修改文件：
- `src/main/java/soj/biclique/TopologyArgs.java`
- `src/main/java/soj/util/FileWriter.java`

baseline 修改文件：
- `src/main/java/soj/util/FileReader.java`

## 真实仓库 PoC 验证

- 检测模式：`poc_string`
- baseline 状态：`VULNERABLE`
- 补丁后状态：`COMPILE_FAILED`
- baseline 漏洞匹配数：`不可比较`
- 补丁后漏洞匹配数：`不可比较`
