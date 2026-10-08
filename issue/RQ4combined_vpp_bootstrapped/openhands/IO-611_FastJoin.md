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

## Vulnerability Call Chain Guidance

The following call chains identify likely entry points and propagation paths related to the vulnerability. Treat them as important guidance for the repair: carefully inspect the listed methods and classes, verify how the vulnerable behavior or data flows through these paths, and prioritize chain-related code during root-cause analysis and patch development.

The chains may not capture every relevant path, so also consider additional code when supported by the source code and tests. You may deviate from the chains when there is clear technical evidence that a different repair location or approach is more appropriate.

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


## Untrusted Upstream Patch Reference

The following patch is an upstream patch provided only as a potentially useful reference. It is not verified ground truth and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project.

Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. The provided call chains are reliable guidance for locating the vulnerable behavior in the downstream project. The upstream patch may use a different implementation or repair location, so independently determine how, or whether, its intended fix should be adapted to the downstream codebase.

Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix.

The final output must be a code change/patch applied to the downstream project.

```diff
diff --git a/src/main/java/org/apache/commons/io/FilenameUtils.java b/src/main/java/org/apache/commons/io/FilenameUtils.java
index 9cddebb..1306662 100644
--- a/src/main/java/org/apache/commons/io/FilenameUtils.java
+++ b/src/main/java/org/apache/commons/io/FilenameUtils.java
@@ -380,7 +380,7 @@ private static String doNormalize(final String filename, final char separator, f
         }
 
         // adjoining slashes
-        for (int i = prefix + 1; i < size; i++) {
+        for (int i = prefix != 0 ? prefix : 1; i < size; i++) {
             if (array[i] == separator && array[i - 1] == separator) {
                 System.arraycopy(array, i, array, i - 1, size - i);
                 size--;
diff --git a/src/test/java/org/apache/commons/io/FilenameUtilsTestCase.java b/src/test/java/org/apache/commons/io/FilenameUtilsTestCase.java
index 234c25e..a107f5d 100644
--- a/src/test/java/org/apache/commons/io/FilenameUtilsTestCase.java
+++ b/src/test/java/org/apache/commons/io/FilenameUtilsTestCase.java
@@ -244,6 +244,8 @@ public void testNormalize() throws Exception {
         assertEquals(null, FilenameUtils.normalize("//server/../a"));
         assertEquals(null, FilenameUtils.normalize("//server/.."));
         assertEquals(SEP + SEP + "server" + SEP + "", FilenameUtils.normalize("//server/"));
+        assertEquals(SEP + SEP + "server" + SEP + "a" + SEP + "b" + SEP, FilenameUtils.normalize("//server//a//b//"));
+        assertEquals(SEP + SEP + "server" + SEP + "bar", FilenameUtils.normalize("//server//./bar"));
     }
 
     @Test
```

Fix this vulnerability in the downstream project.

Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.


Before modifying code, inspect the downstream repository and edit only existing production source files. Do not create or modify a path from the upstream patch if it does not exist downstream; instead, apply the mitigation at an existing downstream caller or wrapper. Verify that every new symbol, method, and import exists and that the resulting code compiles.
