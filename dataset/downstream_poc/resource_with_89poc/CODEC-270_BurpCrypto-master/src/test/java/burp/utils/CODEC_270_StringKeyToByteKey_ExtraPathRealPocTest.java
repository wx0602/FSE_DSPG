package burp.utils;

import org.junit.Test;

public class CODEC_270_StringKeyToByteKey_ExtraPathRealPocTest {

    @Test
    public void stringKeyToByteKeyDecodesIllegalTrailingBits() {
        new CODEC_270_BurpCryptoMaster_PocTest_ExtraPath()
                .stringKeyToByteKeyDecodesIllegalTrailingBits();
    }
}
