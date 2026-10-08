package burp.utils;

import org.junit.Test;

public class CODEC_270_Sm4Decrypt_ExtraPathRealPocTest {

    @Test
    public void sm4DecryptEvaluatesMalformedBase64BeforeMissingCryptoFailure() {
        new CODEC_270_BurpCryptoMaster_PocTest_ExtraPath()
                .sm4DecryptEvaluatesMalformedBase64BeforeMissingCryptoFailure();
    }
}
