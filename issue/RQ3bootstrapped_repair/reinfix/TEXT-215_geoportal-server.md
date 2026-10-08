# Vulnerability Fix Task: TEXT-215_geoportal-server

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`TEXT-215_geoportal-server`

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

## Untrusted Upstream Patch Reference

The following patch was generated for the upstream library and is provided only as a potentially useful reference. It is **not verified ground truth** and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project. Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. Use the reference patch to identify the intended security fix and adapt the relevant changes to the downstream implementation. Do not assume that the reference patch can be applied directly; it may require modification due to differences in code structure, APIs, or dependency versions. Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix. The final output should be a code change/patch applied to the downstream project.

```diff
diff --git a/repo/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java b/repo/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java
index 0000000..0000000 100644
--- a/repo/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java
+++ b/repo/src/main/java/org/apache/commons/text/translate/NumericEntityUnescaper.java
@@ -77,61 +77,67 @@
-    @Override
-    public int translate(final CharSequence input, final int index, final Writer out) throws IOException {
-        final int seqEnd = input.length();
-        // Uses -2 to ensure there is something after the &#
-        if (input.charAt(index) == '&' && index < seqEnd - 2 && input.charAt(index + 1) == '#') {
-            int start = index + 2;
-            boolean isHex = false;
-
-            final char firstChar = input.charAt(start);
-            if (firstChar == 'x' || firstChar == 'X') {
-                start++;
-                isHex = true;
-
-                // Check there's more than just an x after the &#
-                if (start == seqEnd) {
-                    return 0;
-                }
-            }
-
-            int end = start;
-            // Note that this supports character codes without a ; on the end
-            while (end < seqEnd && (input.charAt(end) >= '0' && input.charAt(end) <= '9'
-                                    || input.charAt(end) >= 'a' && input.charAt(end) <= 'f'
-                                    || input.charAt(end) >= 'A' && input.charAt(end) <= 'F')) {
-                end++;
-            }
-
-            final boolean semiNext = end != seqEnd && input.charAt(end) == ';';
-
-            if (!semiNext) {
-                if (isSet(OPTION.semiColonRequired)) {
-                    return 0;
-                }
-                if (isSet(OPTION.errorIfNoSemiColon)) {
-                    throw new IllegalArgumentException("Semi-colon required at end of numeric entity");
-                }
-            }
-
-            int entityValue;
-            try {
-                if (isHex) {
-                    entityValue = Integer.parseInt(input.subSequence(start, end).toString(), 16);
-                } else {
-                    entityValue = Integer.parseInt(input.subSequence(start, end).toString(), 10);
-                }
-            } catch (final NumberFormatException nfe) {
-                return 0;
-            }
-
-            if (entityValue > 0xFFFF) {
-                final char[] chrs = Character.toChars(entityValue);
-                out.write(chrs[0]);
-                out.write(chrs[1]);
-            } else {
-                out.write(entityValue);
-            }
-
-            return 2 + end - start + (isHex ? 1 : 0) + (semiNext ? 1 : 0);
-        }
-        return 0;
-    }
+@Override
+public int translate(final CharSequence input, final int index, final Writer out) throws IOException {
+    final int seqEnd = input.length();
+    // Uses -2 to ensure there is something after the &#
+    if (input.charAt(index) == '&' && index < seqEnd - 2 && input.charAt(index + 1) == '#') {
+        int start = index + 2;
+        boolean isHex = false;
+
+        final char firstChar = input.charAt(start);
+        if (firstChar == 'x' || firstChar == 'X') {
+            start++;
+            isHex = true;
+
+            // Check there's more than just an x after the &#
+            if (start == seqEnd) {
+                return 0;
+            }
+        }
+
+        int end = start;
+        // Note that this supports character codes without a ; on the end
+        if (isHex) {
+            while (end < seqEnd && (input.charAt(end) >= '0' && input.charAt(end) <= '9'
+                                    || input.charAt(end) >= 'a' && input.charAt(end) <= 'f'
+                                    || input.charAt(end) >= 'A' && input.charAt(end) <= 'F')) {
+                end++;
+            }
+        } else {
+            while (end < seqEnd && input.charAt(end) >= '0' && input.charAt(end) <= '9') {
+                end++;
+            }
+        }
+
+        final boolean semiNext = end != seqEnd && input.charAt(end) == ';';
+
+        if (!semiNext) {
+            if (isSet(OPTION.semiColonRequired)) {
+                return 0;
+            }
+            if (isSet(OPTION.errorIfNoSemiColon)) {
+                throw new IllegalArgumentException("Semi-colon required at end of numeric entity");
+            }
+        }
+
+        int entityValue;
+        try {
+            if (isHex) {
+                entityValue = Integer.parseInt(input.subSequence(start, end).toString(), 16);
+            } else {
+                entityValue = Integer.parseInt(input.subSequence(start, end).toString(), 10);
+            }
+        } catch (final NumberFormatException nfe) {
+            return 0;
+        }
+
+        if (entityValue > 0xFFFF) {
+            final char[] chrs = Character.toChars(entityValue);
+            out.write(chrs[0]);
+            out.write(chrs[1]);
+        } else {
+            out.write(entityValue);
+        }
+
+        return 2 + end - start + (isHex ? 1 : 0) + (semiNext ? 1 : 0);
+    }
+    return 0;
+}
```

Fix this vulnerability in the downstream project. Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.
