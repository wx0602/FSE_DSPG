package com.magneto;

import org.apache.commons.lang3.math.NumberUtils;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class LANG_1484_Testcase1 {

    @Test(timeout = 60000)
    public void isParsableAcceptsTrailingDecimalPoint() {
        String input = "100.";
        assertEquals(100.0d, Double.parseDouble(input), 0.0d);
        boolean parsable = NumberUtils.isParsable(input);
        validateReturnValue(parsable);
    }

    public void validateReturnValue(boolean parsable) {
        assertTrue(parsable);
    }
}
