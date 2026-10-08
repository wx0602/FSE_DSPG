# Vulnerability Fix Task: TEXT-215_geoportal-esri

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`TEXT-215_geoportal-esri`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
Description:
A security breach can be used in the NumericEntityUnescaper through the use of decimal character entities.
At line 117 a string of hexadecimal characters are searched, whether or not the entity is an hexadecimal one.
Therefore, if the "semiColonOptional" option is enabled and a deicmal entity without semi-colon is immediately followed by one or several letters from A to F, these letters will be caught. The Integer parsing with a radix at 10 will then fail and the whole entity will be ignored.
Example:
If one uses the following string: 
<iframe src=\"&#106avascript:alert(1)\">
The sequence identifying the entity will wrongly be "&#106a" instead of "&#106".
As "&#106a" is not a valid decimal entity, its Integer parsing fails and the whole entity remains escaped.
Such code would then trigger the alert on all modern browsers.
Solution:
The fix for this is to restrict hexadecimal characters to hexadecimal entities and decimal characters to decimal entities.

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

## Vulnerability Call Chain Guidance

The following call chains identify likely entry points and propagation paths related to the vulnerability. Treat them as important guidance for the repair: carefully inspect the listed methods and classes, verify how the vulnerable behavior or data flows through these paths, and prioritize chain-related code during root-cause analysis and patch development.

The chains may not capture every relevant path, so also consider additional code when supported by the source code and tests. You may deviate from the chains when there is clear technical evidence that a different repair location or approach is more appropriate.

```text
Public Method 1

Method: <com.esri.geoportal.base.util.Val: java.lang.String unescape(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>

2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeOctal(java.lang.String)>

3. <com.esri.geoportal.base.util.Val: java.lang.String unescape(java.lang.String)>

Public Method 2

Method: <com.esri.geoportal.base.util.Val: java.lang.String unescapeNunmericEntity(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>

2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeNunmericEntity(java.lang.String)>

Public Method 3

Method: <com.esri.geoportal.base.util.Val: java.lang.String unescapeOctalToUnicode(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>

2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeOctalToUnicode(java.lang.String)>

Public Method 4

Method: <com.esri.geoportal.base.util.Val: java.lang.String unescapeUnicode(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>

2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeUnicode(java.lang.String)>
```


## Untrusted Upstream Patch Reference

The following patch is an upstream patch provided only as a potentially useful reference. It is not verified ground truth and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project.

Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. The provided call chains are reliable guidance for locating the vulnerable behavior in the downstream project. The upstream patch may use a different implementation or repair location, so independently determine how, or whether, its intended fix should be adapted to the downstream codebase.

Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix.

The final output must be a code change/patch applied to the downstream project.

```diff
diff --git a/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java b/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java
index 54aaec4..9ded127 100644
--- a/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java
+++ b/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java
@@ -112,6 +112,16 @@ public class NumericEntityUnescaper extends CharSequenceTranslator {
                 }
             }
 
+            if (isHex) {
+                while (end < len && isHexDigit(input.charAt(end))) {
+                    end++;
+                }
+            } else {
+                while (end < len && Character.isDigit(input.charAt(end))) {
+                    end++;
+                }
+            }
+
             int entityValue;
             try {
                 if (isHex) {
@@ -135,4 +145,4 @@ public class NumericEntityUnescaper extends CharSequenceTranslator {
         }
         return 0;
     }
-}
+}
```

Fix this vulnerability in the downstream project.

Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.


Use only the downstream repository code already provided in the context and edit only existing production source files. If an upstream patch path does not exist downstream, apply the mitigation at an existing downstream caller or wrapper. Return only a valid patch in the required format; do not describe future inspection or actions. Ensure every new symbol, method, and import exists and that the modified code compiles.
