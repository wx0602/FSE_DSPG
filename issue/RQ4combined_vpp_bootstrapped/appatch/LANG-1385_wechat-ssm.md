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

## Vulnerability Call Chain Guidance

The following call chains identify likely entry points and propagation paths related to the vulnerability. Treat them as important guidance for the repair: carefully inspect the listed methods and classes, verify how the vulnerable behavior or data flows through these paths, and prioritize chain-related code during root-cause analysis and patch development.

The chains may not capture every relevant path, so also consider additional code when supported by the source code and tests. You may deviate from the chains when there is clear technical evidence that a different repair location or approach is more appropriate.

```text
Public Method 1

Method: <cn.qs.utils.format.MyNumberUtils: java.lang.String toFixedDecimal(java.lang.String,int)>

Shortest reverse path from source:

1. <org.apache.commons.lang3.math.NumberUtils: java.lang.Number createNumber(java.lang.String)>

2. <cn.qs.utils.format.MyNumberUtils: java.lang.String toFixedDecimal(java.lang.String,int)>

Public Method 2

Method: <cn.qs.utils.format.MyNumberUtils: java.lang.String toFixedDecimalWithPercent(java.lang.String,int)>

Shortest reverse path from source:

1. <org.apache.commons.lang3.math.NumberUtils: java.lang.Number createNumber(java.lang.String)>

2. <cn.qs.utils.format.MyNumberUtils: java.lang.String toFixedDecimalWithPercent(java.lang.String,int)>
```


## Untrusted Upstream Patch Reference

The following patch is an upstream patch provided only as a potentially useful reference. It is not verified ground truth and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project.

Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. The provided call chains are reliable guidance for locating the vulnerable behavior in the downstream project. The upstream patch may use a different implementation or repair location, so independently determine how, or whether, its intended fix should be adapted to the downstream codebase.

Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix.

The final output must be a code change/patch applied to the downstream project.

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

Fix this vulnerability in the downstream project.

Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.


Before modifying code, inspect the downstream repository and edit only existing production source files. Do not create or modify a path from the upstream patch if it does not exist downstream; instead, apply the mitigation at an existing downstream caller or wrapper. Verify that every new symbol, method, and import exists and that the resulting code compiles.
