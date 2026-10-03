package com.esri.geoportal.base.util;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class Val_TEXT215_Test {

    @Test
    public void shouldTrigger_TEXT215_numericEntityFollowedByLetter() {
        // Original payload
        String input = "<iframe src=\"&#106asafe.example/path\">";

        // Print input value for debugging
        System.out.println("===== Debug Information =====");
        System.out.println("Input Value: " + input);
        System.out.println("Input Value Length: " + input.length());

        String output = Val.unescapeNunmericEntity(input);

        // Print output value for debugging
        System.out.println("Output Value: " + output);
        System.out.println("Output Value Length: " + output.length());
        System.out.println("============================");

        // Assert that input and output are equal
        assertEquals(input, output);
    }
}

