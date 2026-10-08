# Vulnerability Fix Task: IO-611_velocity-engine

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`IO-611_velocity-engine`

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

Method: <org.apache.velocity.runtime.RuntimeInstance: java.lang.String getLoaderNameForResource(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: java.lang.String getLoaderNameForResource(java.lang.String)>

5. <org.apache.velocity.runtime.RuntimeInstance: java.lang.String getLoaderNameForResource(java.lang.String)>

Public Method 2

Method: <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

7. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String)>

Public Method 3

Method: <org.apache.velocity.runtime.RuntimeSingleton: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

7. <org.apache.velocity.runtime.RuntimeSingleton: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

Public Method 4

Method: <org.apache.velocity.runtime.parser.node.ASTDirective: boolean render(org.apache.velocity.context.InternalContextAdapter,java.io.Writer)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

7. <org.apache.velocity.runtime.directive.Parse: boolean render(org.apache.velocity.context.InternalContextAdapter,java.io.Writer,org.apache.velocity.runtime.parser.node.Node)>

8. <org.apache.velocity.runtime.parser.node.ASTDirective: boolean render(org.apache.velocity.context.InternalContextAdapter,java.io.Writer)>

Public Method 5

Method: <org.apache.velocity.app.VelocityEngine: boolean mergeTemplate(java.lang.String,java.lang.String,org.apache.velocity.context.Context,java.io.Writer)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

7. <org.apache.velocity.app.VelocityEngine: boolean mergeTemplate(java.lang.String,java.lang.String,org.apache.velocity.context.Context,java.io.Writer)>

Public Method 6

Method: <org.apache.velocity.app.VelocityEngine: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

7. <org.apache.velocity.app.VelocityEngine: org.apache.velocity.Template getTemplate(java.lang.String,java.lang.String)>

Public Method 7

Method: <org.apache.velocity.runtime.RuntimeSingleton: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String,java.lang.String)>

7. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String)>

8. <org.apache.velocity.runtime.RuntimeSingleton: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String)>

Public Method 8

Method: <org.apache.velocity.runtime.RuntimeSingleton: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String,java.lang.String)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String,java.lang.String)>

7. <org.apache.velocity.runtime.RuntimeSingleton: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String,java.lang.String)>

Public Method 9

Method: <org.apache.velocity.runtime.directive.Include: boolean render(org.apache.velocity.context.InternalContextAdapter,java.io.Writer,org.apache.velocity.runtime.parser.node.Node)>

Shortest reverse path from source:

1. <org.apache.commons.io.FilenameUtils: java.lang.String normalize(java.lang.String)>

2. <org.apache.velocity.runtime.resource.loader.FileResourceLoader: boolean resourceExists(java.lang.String)>

3. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.loader.ResourceLoader getLoaderForResource(java.lang.String)>

4. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource refreshResource(org.apache.velocity.runtime.resource.Resource,java.lang.String)>

5. <org.apache.velocity.runtime.resource.ResourceManagerImpl: org.apache.velocity.runtime.resource.Resource getResource(java.lang.String,int,java.lang.String)>

6. <org.apache.velocity.runtime.RuntimeInstance: org.apache.velocity.runtime.resource.ContentResource getContent(java.lang.String,java.lang.String)>

7. <org.apache.velocity.runtime.directive.Include: boolean renderOutput(org.apache.velocity.runtime.parser.node.Node,org.apache.velocity.context.InternalContextAdapter,java.io.Writer)>

8. <org.apache.velocity.runtime.directive.Include: boolean render(org.apache.velocity.context.InternalContextAdapter,java.io.Writer,org.apache.velocity.runtime.parser.node.Node)>
```


## Untrusted Upstream Patch Reference

The following patch is an upstream patch provided only as a potentially useful reference. It is not verified ground truth and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project.

Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. The provided call chains are reliable guidance for locating the vulnerable behavior in the downstream project. The upstream patch may use a different implementation or repair location, so independently determine how, or whether, its intended fix should be adapted to the downstream codebase.

Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix.

The final output must be a code change/patch applied to the downstream project.

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

Fix this vulnerability in the downstream project.

Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.


Before modifying code, inspect the downstream repository and edit only existing production source files. Do not create or modify a path from the upstream patch if it does not exist downstream; instead, apply the mitigation at an existing downstream caller or wrapper. Verify that every new symbol, method, and import exists and that the resulting code compiles.
