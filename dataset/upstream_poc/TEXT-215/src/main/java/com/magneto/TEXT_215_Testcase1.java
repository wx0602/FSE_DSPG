package com.magneto;

import org.apache.commons.text.translate.NumericEntityUnescaper;
import org.junit.Test;

import java.io.StringWriter;

import static org.junit.Assert.assertEquals;

public class TEXT_215_Testcase1 {

    @Test(timeout = 60000)
    public void decimalEntityStopsBeforeFollowingHexLetter() throws Exception {
        String input = "&#106avascript:alert(1)";
        StringWriter writer = new StringWriter();
        NumericEntityUnescaper unescaper = new NumericEntityUnescaper(NumericEntityUnescaper.OPTION.semiColonOptional);
        unescaper.translate(input, writer);
        validateReturnValue(writer.toString());
    }

    public void validateReturnValue(String output) {
        assertEquals("javascript:alert(1)", output);
    }
}
