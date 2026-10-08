package burp.utils;

import org.junit.Test;

public class CODEC_270_DesDecrypt_ExtraPathRealPocTest {

    @Test
    public void desDecryptReachesMalformedBase64DecodeBeforeCipherFailure() {
        new CODEC_270_BurpCryptoMaster_PocTest_ExtraPath()
                .desDecryptReachesMalformedBase64DecodeBeforeCipherFailure();
    }
}
