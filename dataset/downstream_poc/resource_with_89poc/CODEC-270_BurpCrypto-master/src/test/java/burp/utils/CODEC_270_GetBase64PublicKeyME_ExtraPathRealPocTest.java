package burp.utils;

import org.junit.Test;

public class CODEC_270_GetBase64PublicKeyME_ExtraPathRealPocTest {

    @Test
    public void getBase64PublicKeyMEAcceptsIllegalBase64BeforeKeySpecValidation() throws Exception {
        new CODEC_270_BurpCryptoMaster_PocTest_ExtraPath()
                .getBase64PublicKeyMEAcceptsIllegalBase64BeforeKeySpecValidation();
    }
}
