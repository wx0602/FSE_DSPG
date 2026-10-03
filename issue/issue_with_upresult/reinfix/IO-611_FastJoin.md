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

## Untrusted Upstream Patch Reference

The following patch was generated for the upstream library and is provided only as a potentially useful reference. It is **not verified ground truth** and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project. Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. Use the reference patch to identify the intended security fix and adapt the relevant changes to the downstream implementation. Do not assume that the reference patch can be applied directly; it may require modification due to differences in code structure, APIs, or dependency versions. Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix. The final output should be a code change/patch applied to the downstream project.

```diff
diff --git a/repo/src/main/java/org/apache/commons/io/FilenameUtils.java b/repo/src/main/java/org/apache/commons/io/FilenameUtils.java
index 0000000..0000000 100644
--- a/repo/src/main/java/org/apache/commons/io/FilenameUtils.java
+++ b/repo/src/main/java/org/apache/commons/io/FilenameUtils.java
@@ -348,95 +348,95 @@
-    private static String doNormalize(final String filename, final char separator, final boolean keepSeparator) {
-        if (filename == null) {
-            return null;
-        }
-
-        failIfNullBytePresent(filename);
-
-        int size = filename.length();
-        if (size == 0) {
-            return filename;
-        }
-        final int prefix = getPrefixLength(filename);
-        if (prefix < 0) {
-            return null;
-        }
-
-        final char[] array = new char[size + 2];  // +1 for possible extra slash, +2 for arraycopy
-        filename.getChars(0, filename.length(), array, 0);
-
-        // fix separators throughout
-        final char otherSeparator = separator == SYSTEM_SEPARATOR ? OTHER_SEPARATOR : SYSTEM_SEPARATOR;
-        for (int i = 0; i < array.length; i++) {
-            if (array[i] == otherSeparator) {
-                array[i] = separator;
-            }
-        }
-
-        // add extra separator on the end to simplify code below
-        boolean lastIsDirectory = true;
-        if (array[size - 1] != separator) {
-            array[size++] = separator;
-            lastIsDirectory = false;
-        }
-
-        // adjoining slashes
-        for (int i = prefix + 1; i < size; i++) {
-            if (array[i] == separator && array[i - 1] == separator) {
-                System.arraycopy(array, i, array, i - 1, size - i);
-                size--;
-                i--;
-            }
-        }
-
-        // dot slash
-        for (int i = prefix + 1; i < size; i++) {
-            if (array[i] == separator && array[i - 1] == '.' &&
-                    (i == prefix + 1 || array[i - 2] == separator)) {
-                if (i == size - 1) {
-                    lastIsDirectory = true;
-                }
-                System.arraycopy(array, i + 1, array, i - 1, size - i);
-                size -=2;
-                i--;
-            }
-        }
-
-        // double dot slash
-        outer:
-        for (int i = prefix + 2; i < size; i++) {
-            if (array[i] == separator && array[i - 1] == '.' && array[i - 2] == '.' &&
-                    (i == prefix + 2 || array[i - 3] == separator)) {
-                if (i == prefix + 2) {
-                    return null;
-                }
-                if (i == size - 1) {
-                    lastIsDirectory = true;
-                }
-                int j;
-                for (j = i - 4 ; j >= prefix; j--) {
-                    if (array[j] == separator) {
-                        // remove b/../ from a/b/../c
-                        System.arraycopy(array, i + 1, array, j + 1, size - i);
-                        size -= i - j;
-                        i = j + 1;
-                        continue outer;
-                    }
-                }
-                // remove a/../ from a/../c
-                System.arraycopy(array, i + 1, array, prefix, size - i);
-                size -= i + 1 - prefix;
-                i = prefix + 1;
-            }
-        }
-
-        if (size <= 0) {  // should never be less than 0
-            return "";
-        }
-        if (size <= prefix) {  // should never be less than prefix
-            return new String(array, 0, size);
-        }
-        if (lastIsDirectory && keepSeparator) {
-            return new String(array, 0, size);  // keep trailing separator
-        }
-        return new String(array, 0, size - 1);  // lose trailing separator
-    }
+private static String doNormalize(final String filename, final char separator, final boolean keepSeparator) {
+    if (filename == null) {
+        return null;
+    }
+
+    failIfNullBytePresent(filename);
+
+    int size = filename.length();
+    if (size == 0) {
+        return filename;
+    }
+    final int prefix = getPrefixLength(filename);
+    if (prefix < 0) {
+        return null;
+    }
+
+    final char[] array = new char[size + 2];  // +1 for possible extra slash, +2 for arraycopy
+    filename.getChars(0, filename.length(), array, 0);
+
+    // fix separators throughout
+    final char otherSeparator = separator == SYSTEM_SEPARATOR ? OTHER_SEPARATOR : SYSTEM_SEPARATOR;
+    for (int i = 0; i < array.length; i++) {
+        if (array[i] == otherSeparator) {
+            array[i] = separator;
+        }
+    }
+
+    // add extra separator on the end to simplify code below
+    boolean lastIsDirectory = true;
+    if (array[size - 1] != separator) {
+        array[size++] = separator;
+        lastIsDirectory = false;
+    }
+
+    // collapse repeated separators after the prefix
+    for (int i = prefix + 1; i < size; i++) {
+        if (array[i] == separator && array[i - 1] == separator) {
+            System.arraycopy(array, i, array, i - 1, size - i);
+            size--;
+            i--;
+        }
+    }
+
+    // dot slash
+    for (int i = prefix + 1; i < size; i++) {
+        if (array[i] == separator && array[i - 1] == '.' &&
+                (i == prefix + 1 || array[i - 2] == separator)) {
+            if (i == size - 1) {
+                lastIsDirectory = true;
+            }
+            System.arraycopy(array, i + 1, array, i - 1, size - i);
+            size -= 2;
+            i--;
+        }
+    }
+
+    // double dot slash
+    outer:
+    for (int i = prefix + 2; i < size; i++) {
+        if (array[i] == separator && array[i - 1] == '.' && array[i - 2] == '.' &&
+                (i == prefix + 2 || array[i - 3] == separator)) {
+            if (i == prefix + 2) {
+                return null;
+            }
+            if (i == size - 1) {
+                lastIsDirectory = true;
+            }
+            int j;
+            for (j = i - 4 ; j >= prefix; j--) {
+                if (array[j] == separator) {
+                    // remove b/../ from a/b/../c
+                    System.arraycopy(array, i + 1, array, j + 1, size - i);
+                    size -= i - j;
+                    i = j + 1;
+                    continue outer;
+                }
+            }
+            // remove a/../ from a/../c
+            System.arraycopy(array, i + 1, array, prefix, size - i);
+            size -= i + 1 - prefix;
+            i = prefix + 1;
+        }
+    }
+
+    if (size <= 0) {  // should never be less than 0
+        return "";
+    }
+    if (size <= prefix) {  // should never be less than prefix
+        return new String(array, 0, size);
+    }
+    if (lastIsDirectory && keepSeparator) {
+        return new String(array, 0, size);  // keep trailing separator
+    }
+    return new String(array, 0, size - 1);  // lose trailing separator
+}
```

Fix this vulnerability in the downstream project. Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.
