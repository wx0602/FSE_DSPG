package com.magneto;

import org.apache.commons.codec.binary.Base64;
import org.junit.Test;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

public class CODEC_263_Testcase1 {

    @Test(timeout = 60000)
    public void decodeBase64ShouldMatchIsBase64Decision() {
        String input = "publishMessage";
        assertTrue(Base64.isBase64(input));

        try {
            byte[] decoded = Base64.decodeBase64(input);
            validateReturnValue(decoded);
        } catch (IllegalArgumentException e) {
            validateThrow(e);
        }
    }

    public void validateReturnValue(byte[] decoded) {
        assertNotNull(decoded);
    }

    public void validateThrow(Throwable e) {
        fail("Base64.decodeBase64 should not reject input accepted by Base64.isBase64: " + e);
    }
}
