package com.esri.geoportal.base.util;

import org.junit.Test;

public class TEXT_215_GeoportalServer_UnescapeNumericEntity_ExtraPathRealPocTest {

    @Test
    public void numericEntityFollowedByHexLetterIsLeftEscaped() {
        new TEXT_215_GeoportalServer_PocTest_ExtraPath()
                .numericEntityFollowedByHexLetterIsLeftEscaped();
    }
}
