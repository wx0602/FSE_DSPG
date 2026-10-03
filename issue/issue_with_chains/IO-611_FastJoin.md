# Vulnerability Fix Task: IO-611_FastJoin

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`IO-611_FastJoin`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
FilenameUtils.normalize does not sanitize multiple slashes after prefix






Export

Details

Type: Bug
Status:Resolved
Priority: Major
Resolution:Fixed
Affects Version/s:2.6
Fix Version/s:2.12.0
Component/s:None
Labels:
None

Description

FilenameUtils.#normalize states in javadoc that //foo//./bar becomes /foo/bar
System.out.println(FilenameUtils.normalize("//foo//./bar"));
System.out.println(FilenameUtils.normalize("\\\\foo\\\\.\\bar"));
Result:
//foo//bar
//foo//bar
So, javadoc says, that it should be /foo/bar. I think, that //foo is prefix, so it should be //foo/bar. But in real life it becomes the third way (//foo//bar).

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

fix this vulnerability. Even if the fix fails, you must still modify the code in the best possible way.

## Vulnerability Call Chain Guidance

The following call chains identify likely entry points and propagation paths related to the vulnerability. Treat them as important guidance for the repair: carefully inspect the listed methods and classes, verify how the vulnerable behavior or data flows through these paths, and prioritize chain-related code during root-cause analysis and patch development. The chains may not capture every relevant path, so also consider additional code when supported by the source code and tests. You may deviate from the chains when there is clear technical evidence that a different repair location or approach is more appropriate.

```text
Public Method 1
Method: <soj.util.FileWriter: void <init>(java.lang.String,java.lang.String,java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>
2. <soj.util.FileWriter: java.lang.String constructFilename(java.lang.String,java.lang.String,java.lang.String)>
3. <soj.util.FileWriter: void <init>(java.lang.String,java.lang.String,java.lang.String)>

Public Method 2
Method: <soj.util.FileWriter: void <init>(java.lang.String,java.lang.String,java.lang.String,boolean)>
Shortest reverse path from source:
1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>
2. <soj.util.FileWriter: java.lang.String constructFilename(java.lang.String,java.lang.String,java.lang.String)>
3. <soj.util.FileWriter: void <init>(java.lang.String,java.lang.String,java.lang.String,boolean)>

Public Method 3
Method: <soj.util.FileReader: void <init>(java.lang.String,java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>
2. <soj.util.FileReader: void <init>(java.lang.String,java.lang.String)>

Public Method 4
Method: <soj.util.FileWriter: void <init>(java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>
2. <soj.util.FileWriter: void <init>(java.lang.String)>

Public Method 5
Method: <soj.util.FileWriter: void <init>(java.lang.String,boolean)>
Shortest reverse path from source:
1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>
2. <soj.util.FileWriter: void <init>(java.lang.String,boolean)>
```
