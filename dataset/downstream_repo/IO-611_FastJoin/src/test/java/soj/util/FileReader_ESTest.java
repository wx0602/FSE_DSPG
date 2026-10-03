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
