# Vulnerability Fix Task: IO-611_FastJoin

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

A proof-of-concept (PoC) is provided at the end of this issue. Use it as a concrete reference to understand how the vulnerability is triggered, trace the affected downstream code path, and validate your repair. Do not hard-code a fix only for the exact PoC input; address the underlying vulnerability while preserving intended functionality.

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

fix this vulnerability. Even if the fix fails, you must still modify the code in the best possible way.

## Proof of Concept (PoC) Reference

The following PoC demonstrates a known way to exercise the vulnerable behavior in this project. Treat it as repair and validation guidance; inspect the surrounding implementation and related input variants as well.

```java
// ------------------------------------------------------------------------------------------------
// Source: src/test/java/soj/util/FileReader_ESTest.java
// ------------------------------------------------------------------------------------------------

package soj.util;

import org.junit.Test;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.Assert.*;

public class FileReader_ESTest {

    @Test(timeout = 4000L)
    public void fileReader_entry_shouldNormalizePathCorrectly_IO611() throws Throwable {
        Path dir = Files.createTempDirectory("io611_fastjoin_");
        Path file = dir.resolve("ok.txt");
        Files.write(file, "OK".getBytes(StandardCharsets.UTF_8));

        try {
            String abs = file.toAbsolutePath().toString().replace('\\', '/');
            String input = toIo611ShapedPath(abs);

            // Business entry: FileReader ctor calls FilenameUtils.normalize(...)
            FileReader fr = new FileReader(input, "UTF-8");

            String normalized = extractFilename(fr);

            // Expected fixed behavior: collapse extra '//' after prefix and remove './'
            String expected = expectedFixed(abs);
            assertEquals(expected, normalized);
        } finally {
            try { Files.deleteIfExists(file); } catch (Exception ignored) {}
            try { Files.deleteIfExists(dir); } catch (Exception ignored) {}
        }
    }

    // Convert "/a/b/c" to IO-611 shaped input: "//a//./b/c"
    private static String toIo611ShapedPath(String absPath) {
        String[] parts = absPath.split("/");
        if (parts.length < 3 || !"".equals(parts[0])) {
            // Fallback if path is unexpected
            return "//foo//./bar";
        }
        String root = parts[1];
        String rest = join(parts, 2, "/");
        return "//" + root + "//./" + rest;
    }

    // Expected fixed: "//a/b/c"
    private static String expectedFixed(String absPath) {
        String[] parts = absPath.split("/");
        if (parts.length < 3 || !"".equals(parts[0])) {
            return "//foo/bar";
        }
        String root = parts[1];
        String rest = join(parts, 2, "/");
        return "//" + root + "/" + rest;
    }

    private static String extractFilename(FileReader fr) throws Exception {
        // Prefer field name "_filename"
        try {
            Field f = fr.getClass().getDeclaredField("_filename");
            f.setAccessible(true);
            Object v = f.get(fr);
            if (v instanceof String) return (String) v;
        } catch (NoSuchFieldException ignored) {}

        // Fallback: scan String fields
        Class<?> c = fr.getClass();
        while (c != null && c != Object.class) {
            for (Field f : c.getDeclaredFields()) {
                if (f.getType() == String.class) {
                    f.setAccessible(true);
                    Object v = f.get(fr);
                    if (v instanceof String) {
                        String s = (String) v;
                        if (s.startsWith("//") && s.contains("ok.txt")) {
                            return s;
                        }
                    }
                }
            }
            c = c.getSuperclass();
        }

        fail("Cannot extract normalized filename from FileReader.");
        return null;
    }

    private static String join(String[] arr, int start, String sep) {
        StringBuilder sb = new StringBuilder();
        for (int i = start; i < arr.length; i++) {
            if (arr[i] == null || arr[i].isEmpty()) continue;
            if (sb.length() > 0) sb.append(sep);
            sb.append(arr[i]);
        }
        return sb.toString();
    }
}
```
