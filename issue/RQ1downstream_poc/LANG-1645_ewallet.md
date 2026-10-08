# Vulnerability Fix Task: LANG-1645_ewallet

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

A proof-of-concept (PoC) is provided at the end of this issue. Use it as a concrete reference to understand how the vulnerability is triggered, trace the affected downstream code path, and validate your repair. Do not hard-code a fix only for the exact PoC input; address the underlying vulnerability while preserving intended functionality.

## Vulnerability ID

`LANG-1645_ewallet`

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

fix this vulnerability. Even if the fix fails, you must still modify the code in the best possible way.

## Proof of Concept (PoC) Reference

The following PoC demonstrates a known way to exercise the vulnerable behavior in this project. Treat it as repair and validation guidance; inspect the surrounding implementation and related input variants as well.

```java
// ------------------------------------------------------------------------------------------------
// Source: wallet-base/src/test/java/com/fr/chain/utils/LANG_1645_CreateNumber_ExtraPathRealPocTest.java
// ------------------------------------------------------------------------------------------------

package com.fr.chain.utils;

import org.junit.Test;

public class LANG_1645_CreateNumber_ExtraPathRealPocTest {

    @Test
    public void createNumberRejectsSignedHexIntegerAlthoughDecodeAcceptsIt() {
        new LANG_1645_Ewallet_PocTest_ExtraPath()
                .createNumberRejectsSignedHexIntegerAlthoughDecodeAcceptsIt();
    }
}

// ------------------------------------------------------------------------------------------------
// Source: wallet-base/src/test/java/com/fr/chain/utils/NumberUtil_ESTest.java
// ------------------------------------------------------------------------------------------------

package com.fr.chain.utils;

import org.junit.Test;

public class NumberUtil_ESTest {

    @Test
    public void lang1645_plus() {
        // LANG-1645 trigger (client-side):
        // Some vulnerable commons-lang3 versions throw NumberFormatException when parsing
        // plus-prefixed hex strings in createBigInteger, e.g. "+0x10".
        //
        // Expected:
        // - Vulnerable version: throws -> test error -> build FAIL
        // - Fixed version: no exception -> test PASS -> build SUCCESS

        // Do not catch exceptions: any NumberFormatException should fail the build automatically.
        System.out.println("Parsed createBigInteger(+0x10) => " + NumberUtil.createBigInteger("+0x10"));

        // Optional: keep createNumber as a non-failing sanity check (can be removed)
        //System.out.println("Parsed createNumber(+0x10) => " + NumberUtil.createNumber("+0x10"));
    }
}
```
