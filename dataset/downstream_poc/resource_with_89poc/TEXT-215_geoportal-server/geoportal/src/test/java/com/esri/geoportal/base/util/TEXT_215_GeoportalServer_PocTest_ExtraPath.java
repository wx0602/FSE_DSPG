package com.esri.geoportal.base.util;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class TEXT_215_GeoportalServer_PocTest_ExtraPath {

    @Test
    public void numericEntityFollowedByHexLetterIsLeftEscaped() {
        String input = "<iframe src=\"&#106avascript:alert(1)\">";
        String output = Val.unescapeNunmericEntity(input);
        assertEquals(input, output);
    }

    @Test
    public void terminalUnescapeUnicodeDecodesEscapedMarkup() {
        assertEquals("<script>", Val.unescapeUnicode("\\u003cscript\\u003e"));
    }

    @Test
    public void terminalUnescapeOctalToUnicodeDecodesUtf8OctalBytes() {
        assertEquals("é", Val.unescapeOctalToUnicode("\\303\\251"));
    }

    @Test
    public void terminalUnescapeKeepsOctalOnlyInputDueToDownstreamReturnBug() {
        String input = "\\074script\\076";
        assertEquals(input, Val.unescape(input));
    }
}
