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
@@ -751,32 +751,33 @@
      * @return converted <code>BigInteger</code> (or null if the input is null)
      * @throws NumberFormatException if the value cannot be converted
      */
-    public static BigInteger createBigInteger(final String str) {
-        if (str == null) {
-            return null;
-        }
-        int pos = 0; // offset within string
-        int radix = 10;
-        boolean negate = false; // need to negate later?
-        if (str.startsWith("-")) {
-            negate = true;
-            pos = 1;
-        }
-        if (str.startsWith("0x", pos) || str.startsWith("0X", pos)) { // hex
-            radix = 16;
-            pos += 2;
-        } else if (str.startsWith("#", pos)) { // alternative hex (allowed by Long/Integer)
-            radix = 16;
-            pos ++;
-        } else if (str.startsWith("0", pos) && str.length() > pos + 1) { // octal; so long as there are additional digits
-            radix = 8;
-            pos ++;
-        } // default is to treat as decimal
-
-        final BigInteger value = new BigInteger(str.substring(pos), radix);
-        return negate ? value.negate() : value;
-    }
-
+public static BigInteger createBigInteger(final String str) {
+    if (str == null) {
+        return null;
+    }
+    int pos = 0; // offset within string
+    int radix = 10;
+    boolean negate = false; // need to negate later?
+    if (str.startsWith("-")) {
+        negate = true;
+        pos = 1;
+    } else if (str.startsWith("+")) {
+        pos = 1;
+    }
+    if (str.startsWith("0x", pos) || str.startsWith("0X", pos)) { // hex
+        radix = 16;
+        pos += 2;
+    } else if (str.startsWith("#", pos)) { // alternative hex (allowed by Long/Integer)
+        radix = 16;
+        pos ++;
+    } else if (str.startsWith("0", pos) && str.length() > pos + 1) { // octal; so long as there are additional digits
+        radix = 8;
+        pos ++;
+    } // default is to treat as decimal
+
+    final BigInteger value = new BigInteger(str.substring(pos), radix);
+    return negate ? value.negate() : value;
+}
     /**
      * <p>Convert a <code>String</code> to a <code>BigDecimal</code>.</p>
      *
```

Fix this vulnerability in the downstream project.

Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.


Before modifying code, inspect the downstream repository and edit only existing production source files. Do not create or modify a path from the upstream patch if it does not exist downstream; instead, apply the mitigation at an existing downstream caller or wrapper. Verify that every new symbol, method, and import exists and that the resulting code compiles.
