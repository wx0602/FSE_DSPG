# Vulnerability Fix Task: LANG-1645_wechat-ssm

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`LANG-1645_wechat-ssm`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
Description

The Java Language Specification allows an optional sign prefix for a number as + or -.
A + sign before a hex integer is not recognised by createNumber and createBigInteger but is recognised by isCreatable, createInteger and createLong. The two later functions delegate to Java's decode() function that handles an optional leading +.
The following demonstrates the tests that fail but would pass if the leading '+' is removed.
@Test
void testCreatePositiveHexInteger() {
// Hex is only supported for integers so no test for hex floating point formats
assertTrue(NumberUtils.isCreatable("+0xF"));
assertTrue(NumberUtils.isCreatable("+0xFFFFFFFF"));
assertTrue(NumberUtils.isCreatable("+0xFFFFFFFFFFFFFFFFF"));

assertEquals(Integer.decode("+0xF"), NumberUtils.createInteger("+0xF"));
assertEquals(Long.decode("+0xFFFFFFFF"), NumberUtils.createLong("+0xFFFFFFFF"));

assertEquals(new BigInteger("+FFFFFFFFFFFFFFFF", 16),
NumberUtils.createBigInteger("0xFFFFFFFFFFFFFFFF"));
try {
assertEquals(new BigInteger("+FFFFFFFFFFFFFFFF", 16),
NumberUtils.createBigInteger("+0xFFFFFFFFFFFFFFFF"));
Assertions.fail("This should be possible but it is not");
} catch (NumberFormatException ex) {
// This should not happen
}

assertEquals(Integer.decode("+0xF"),
NumberUtils.createNumber("0xF"));
try {
assertEquals(Integer.decode("+0xF"),
NumberUtils.createNumber("+0xF"));
Assertions.fail("This should be possible but it is not");
} catch (NumberFormatException ex) {
// This should not happen
}

assertEquals(Long.decode("+0xFFFFFFFF"),
NumberUtils.createNumber("0xFFFFFFFF"));
try {
assertEquals(Long.decode("+0xFFFFFFFF"),
NumberUtils.createNumber("+0xFFFFFFFF"));
Assertions.fail("This should be possible but it is not");
} catch (NumberFormatException ex) {
// This should not happen
}

assertEquals(new BigInteger("+FFFFFFFFFFFFFFFF", 16),
NumberUtils.createNumber("0xFFFFFFFFFFFFFFFF"));
try {
assertEquals(new BigInteger("+FFFFFFFFFFFFFFFF", 16),
NumberUtils.createNumber("+0xFFFFFFFFFFFFFFFF"));
Assertions.fail("This should be possible but it is not");
} catch (NumberFormatException ex) {
// This should not happen
}
}
A simple fix is to check for a leading '+' character and advance all processing past this character.

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

## Untrusted Upstream Patch Reference

The following patch was generated for the upstream library and is provided only as a potentially useful reference. It is **not verified ground truth** and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project. Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. Use the reference patch to identify the intended security fix and adapt the relevant changes to the downstream implementation. Do not assume that the reference patch can be applied directly; it may require modification due to differences in code structure, APIs, or dependency versions. Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix. The final output should be a code change/patch applied to the downstream project.

```diff
diff --git a/src/main/java/org/apache/commons/lang3/math/NumberUtils.java b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
index 7b3f739..80d7bdb 100644
--- a/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
+++ b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
@@ -456,7 +456,7 @@ public class NumberUtils {
             throw new NumberFormatException("A blank string is not a valid number");
         }
         // Need to deal with all possible hex prefixes here
-        final String[] hex_prefixes = {"0x", "0X", "-0x", "-0X", "#", "-#"};
+        final String[] hex_prefixes = {"0x", "0X", "-0x", "-0X", "+0x", "+0X", "#", "-#", "+#"};
         int pfxLen = 0;
         for(final String pfx : hex_prefixes) {
             if (str.startsWith(pfx)) {
@@ -758,8 +758,8 @@ public class NumberUtils {
         int pos = 0; // offset within string
         int radix = 10;
         boolean negate = false; // need to negate later?
-        if (str.startsWith("-")) {
-            negate = true;
+        if (str.startsWith("-") || str.startsWith("+")) {
+            negate = str.startsWith("-");
             pos = 1;
         }
         if (str.startsWith("0x", pos) || str.startsWith("0X", pos)) { // hex
diff --git a/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java b/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
index 132d71e..ad1ce6e 100644
--- a/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
+++ b/src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java
@@ -269,6 +269,10 @@ public class NumberUtilsTest {
         assertEquals(Long.valueOf(0x80000000L),    NumberUtils.createNumber("0x80000000"));
         assertEquals(Long.valueOf(0xFFFFFFFFL),    NumberUtils.createNumber("0xFFFFFFFF"));
 
+        assertEquals(Integer.valueOf(0xF), NumberUtils.createNumber("+0xF"));
+        assertEquals(Long.valueOf(0xFFFFFFFFL), NumberUtils.createNumber("+0xFFFFFFFF"));
+        assertEquals(new BigInteger("FFFFFFFFFFFFFFFF", 16), NumberUtils.createNumber("+0xFFFFFFFFFFFFFFFF"));
+
         // Leading zero tests
         assertEquals(Integer.valueOf(0x8000000),   NumberUtils.createNumber("0x08000000"));
         assertEquals(Integer.valueOf(0x7FFFFFFF),  NumberUtils.createNumber("0x007FFFFFFF"));
@@ -442,6 +446,7 @@ public class NumberUtilsTest {
         assertEquals("createBigInteger(String) failed", new BigInteger("255"), NumberUtils.createBigInteger("0xff"));
         assertEquals("createBigInteger(String) failed", new BigInteger("255"), NumberUtils.createBigInteger("0Xff"));
         assertEquals("createBigInteger(String) failed", new BigInteger("255"), NumberUtils.createBigInteger("#ff"));
+        assertEquals("createBigInteger(String) failed", new BigInteger("255"), NumberUtils.createBigInteger("+0xff"));
         assertEquals("createBigInteger(String) failed", new BigInteger("-255"), NumberUtils.createBigInteger("-0xff"));
         assertEquals("createBigInteger(String) failed", new BigInteger("255"), NumberUtils.createBigInteger("0377"));
         assertEquals("createBigInteger(String) failed", new BigInteger("-255"), NumberUtils.createBigInteger("-0377"));
```

Fix this vulnerability in the downstream project. Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.
