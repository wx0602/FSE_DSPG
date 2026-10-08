package burp.utils;

import org.junit.Test;

public class CODEC_270_ZucDecrypt_ExtraPathRealPocTest {

    @Test
    public void zucDecryptEvaluatesMalformedBase64BeforeMissingCryptoFailure() {
        new CODEC_270_BurpCryptoMaster_PocTest_ExtraPath()
                .zucDecryptEvaluatesMalformedBase64BeforeMissingCryptoFailure();
    }
}
