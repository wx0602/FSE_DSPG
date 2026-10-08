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
