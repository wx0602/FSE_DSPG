# Vulnerability Fix Task: LANG-1385_wechat-ssm

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`LANG-1385_wechat-ssm`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
Description

Test case:
NumberUtils.createNumber("L")
Expected: NumberFormatException
Got:
java.lang.StringIndexOutOfBoundsException: String index out of range: 0
at java.lang.String.charAt(String.java:658)
at org.apache.commons.lang3.math.NumberUtils.createNumber(NumberUtils.java:528)

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

## Untrusted Upstream Patch Reference

The following patch was generated for the upstream library and is provided only as a potentially useful reference. It is **not verified ground truth** and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project. Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. Use the reference patch to identify the intended security fix and adapt the relevant changes to the downstream implementation. Do not assume that the reference patch can be applied directly; it may require modification due to differences in code structure, APIs, or dependency versions. Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix. The final output should be a code change/patch applied to the downstream project.

```diff
--- a/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
+++ b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
@@ -467,6 +467,9 @@
         if (pfxLen > 0) { // we have a hex number
             char firstSigDigit = 0; // strip leading zeroes
             for(int i = pfxLen; i < str.length(); i++) {
+                if (str.length() == pfxLen) {
+                    throw new NumberFormatException(str + " is not a valid number.");
+                }
                 firstSigDigit = str.charAt(i);
                 if (firstSigDigit == '0') { // count leading zeroes
                     pfxLen++;
@@ -485,6 +488,9 @@
         }
         final char lastChar = str.charAt(str.length() - 1);
         String mant;
+        if (str.length() == 1) {
+            throw new NumberFormatException(str + " is not a valid number.");
+        }
         String dec;
         String exp;
         final int decPos = str.indexOf('.');
--- a/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
+++ b/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
@@ -229,6 +229,12 @@
         assertEquals("createNumber(String) 18 failed", new BigInteger("10" + Long.MAX_VALUE), NumberUtils
                 .createNumber("10" + Long.MAX_VALUE));
 
+        try {
+            NumberUtils.createNumber("L");
+            fail("Expected NumberFormatException");
+        } catch (final NumberFormatException ex) {
+            // expected
+        }
         // LANG-521
         assertEquals("createNumber(String) LANG-521 failed", Float.valueOf("2."), NumberUtils.createNumber("2."));
```

Fix this vulnerability in the downstream project. Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.
