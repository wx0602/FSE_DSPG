package com.fr.chain.utils;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

public class LANG_1645_Ewallet_PocTest_ExtraPath {

    @Test
    public void createNumberRejectsSignedHexIntegerAlthoughDecodeAcceptsIt() {
        assertEquals(Integer.valueOf(15), NumberUtil.createInteger("+0xF"));

        try {
            NumberUtil.createNumber("+0xF");
            fail("LANG-1645 is present when createNumber rejects a valid signed hexadecimal integer.");
        } catch (NumberFormatException expected) {
            assertEquals("+0xF is not a valid number.", expected.getMessage());
        }
    }
}
