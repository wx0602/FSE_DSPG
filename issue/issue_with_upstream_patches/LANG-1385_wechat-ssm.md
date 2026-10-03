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

fix this vulnerability. Even if the fix fails, you must still modify the code in the best possible way.

## Upstream Patch

```diff
diff --git a/repo/src/main/java/org/apache/commons/lang3/math/NumberUtils.java b/repo/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
index 7b3f739..a254766 100644
--- a/repo/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
+++ b/repo/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
@@ -530,6 +530,7 @@ public class NumberUtils {
                 case 'L' :
                     if (dec == null
                         && exp == null
+                        && !numeric.isEmpty()
                         && (numeric.charAt(0) == '-' && isDigits(numeric.substring(1)) || isDigits(numeric))) {
                         try {
                             return createLong(numeric);
```
