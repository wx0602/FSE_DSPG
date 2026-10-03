# Vulnerability Fix Task: LANG-1484_jjdz7-drony-refactor

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`LANG-1484_jjdz7-drony-refactor`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
Description

From the Javadocs:
Parsable numbers include those Strings understood by ... Double.parseDouble(String).
Double.parseDouble("100.") returns a valid double (it does not throw a NumberFormatException); however, NumberUtils.isParsable("100.") returns false.

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

## Untrusted Upstream Patch Reference

The following patch was generated for the upstream library and is provided only as a potentially useful reference. It is **not verified ground truth** and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project. Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. Use the reference patch to identify the intended security fix and adapt the relevant changes to the downstream implementation. Do not assume that the reference patch can be applied directly; it may require modification due to differences in code structure, APIs, or dependency versions. Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix. The final output should be a code change/patch applied to the downstream project.

```diff
diff --git a/src/main/java/org/apache/commons/lang3/math/NumberUtils.java b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
index 4d2d3d7..7e3a1a1 100644
--- a/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
+++ b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
@@ -823,7 +823,7 @@ public class NumberUtils {
                 }
                 foundDigit = true;
 
-            } else if (c == '.') {
+            } else if (c == '.') {
                 if (foundDecimalPoint || foundExponent) {
                     return false;
                 }
@@ -833,6 +833,9 @@ public class NumberUtils {
                 if (!foundDigit) {
                     return false;
                 }
+                if (i == chars.length - 1) {
+                    return true;
+                }
                 foundDecimalPoint = true;
 
             } else if (c == 'e' || c == 'E') {
diff --git a/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java b/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
index 4d8c0a1..dd1b3f3 100644
--- a/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
+++ b/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
@@ -1,5 +1,6 @@
 package org.apache.commons.lang3.math;
 
+import static org.junit.Assert.assertTrue;
 import static org.junit.Assert.assertFalse;
 import static org.junit.Assert.assertEquals;
 
@@ -128,6 +129,7 @@ public class NumberUtilsTest {
     public void testIsParsable() {
         assertFalse(NumberUtils.isParsable(null));
         assertFalse(NumberUtils.isParsable(""));
+        assertTrue(NumberUtils.isParsable("100."));
         assertTrue(NumberUtils.isParsable("0"));
         assertTrue(NumberUtils.isParsable("123"));
         assertTrue(NumberUtils.isParsable("123.45"));
```

Fix this vulnerability in the downstream project. Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.
