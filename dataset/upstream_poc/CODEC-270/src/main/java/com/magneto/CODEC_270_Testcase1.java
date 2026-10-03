package com.magneto;

import org.apache.commons.codec.binary.Base32;
import org.apache.commons.codec.binary.Base64;
import org.junit.Test;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

public class CODEC_270_Testcase1 {

    @Test(timeout = 60000)
    public void base64RejectsImpossibleTrailingBits() {
        try {
            Base64.decodeBase64("AB==");
            fail("fail the test");
        } catch (IllegalArgumentException e) {
            validateThrow(e);
        }
    }

    @Test(timeout = 60000)
    public void base32RejectsImpossibleTrailingBits() {
        try {
            new Base32().decode("AB======");
            fail("fail the test");
        } catch (IllegalArgumentException e) {
            validateThrow(e);
        }
    }

    public void validateThrow(Throwable e) {
        assertTrue(e instanceof IllegalArgumentException);
    }
}
