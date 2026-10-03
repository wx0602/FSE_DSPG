# Vulnerability Fix Task: Zip-263_ZingClient

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`Zip-263_ZingClient`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title.
Current version (2.6.4) allows to construct a with a reference: (i.e. ) without proper validation. This does not happen if you use the constructor with the argument as internally it does a and if the string is the constructor throws a NPE.ZipFilenullFilenew ZipFile((File) null)Stringnew File(string)nullFile
The consequence of this is that when you want to do an operation with the instance (e.g. it throws a NPE on this line.ZipFilezipFile.getFileHeaders()

Current version (2.6.4) allows to construct a ZipFile with a null File reference: (i.e. new ZipFile((File) null)) without proper validation. This does not happen if you use the constructor with the String argument as internally it does a new File(string) and if the string is null the File constructor throws a NPE.
The consequence of this is that when you want to do an operation with the ZipFile instance (e.g. zipFile.getFileHeaders() it throws a NPE on this line.
To avoid these scenarios, it should be properly validated on construction of ZipFile if accepting a null reference as File is not valid later.
On previous versions (1.3.2) there was a check that somehow on later releases it was removed (particularly on this commit).
This is 1.3.2:

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

## Vulnerability Call Chain Guidance

The following call chains identify likely entry points and propagation paths related to the vulnerability. Treat them as important guidance for the repair: carefully inspect the listed methods and classes, verify how the vulnerable behavior or data flows through these paths, and prioritize chain-related code during root-cause analysis and patch development.

The chains may not capture every relevant path, so also consider additional code when supported by the source code and tests. You may deviate from the chains when there is clear technical evidence that a different repair location or approach is more appropriate.

```text
Public Method 1

Method: <ZingClient.zing.client.file.ZFile: void <init>(java.io.File,java.lang.String)>

Shortest reverse path from source:

1. <net.lingala.zip4j.ZipFile: void <init>(java.io.File)>

2. <ZingClient.zing.client.file.ZFile: void <init>(java.io.File,java.lang.String)>
```


## Untrusted Upstream Patch Reference

The following patch is an upstream patch provided only as a potentially useful reference. It is not verified ground truth and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project.

Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. The provided call chains are reliable guidance for locating the vulnerable behavior in the downstream project. The upstream patch may use a different implementation or repair location, so independently determine how, or whether, its intended fix should be adapted to the downstream codebase.

Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix.

The final output must be a code change/patch applied to the downstream project.

```diff
diff --git a/src/main/java/net/lingala/zip4j/ZipFile.java b/src/main/java/net/lingala/zip4j/ZipFile.java
index 6d81966..ccd1730 100755
--- a/src/main/java/net/lingala/zip4j/ZipFile.java
+++ b/src/main/java/net/lingala/zip4j/ZipFile.java
@@ -113,6 +113,10 @@ public class ZipFile {
   }
 
   public ZipFile(File zipFile, char[] password) {
+    if (zipFile == null) {
+      throw new NullPointerException("zipFile");
+    }
+
     this.zipFile = zipFile;
     this.password = password;
     this.runInThread = false;
```

Fix this vulnerability in the downstream project.

Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.


Before modifying code, inspect the downstream repository and edit only existing production source files. Do not create or modify a path from the upstream patch if it does not exist downstream; instead, apply the mitigation at an existing downstream caller or wrapper. Verify that every new symbol, method, and import exists and that the resulting code compiles.
