package burp.utils;

import burp.des.DesAlgorithms;
import burp.des.DesConfig;
import burp.des.DesUtil;
import burp.sm4.SM4Util;
import burp.zuc.ZUCUtil;
import org.junit.Test;

import java.nio.charset.StandardCharsets;
import java.security.spec.InvalidKeySpecException;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

public class CODEC_270_BurpCryptoMaster_PocTest_ExtraPath {

    @Test
    public void utilsBase64DecodesIllegalTrailingBits() {
        assertArrayEquals(new byte[]{0}, Utils.base64("AB=="));
    }

    @Test
    public void stringKeyToByteKeyDecodesIllegalTrailingBits() {
        assertArrayEquals(new byte[]{0}, Utils.StringKeyToByteKey("AB==", KeyFormat.Base64));
    }

    @Test
    public void getBase64PublicKeyMEAcceptsIllegalBase64BeforeKeySpecValidation() throws Exception {
        try {
            Utils.getBase64PublicKeyME("AB==");
            fail("Expected RSA key parsing to fail after Commons Codec accepted the malformed Base64.");
        } catch (InvalidKeySpecException expected) {
            assertTrue(expected.getMessage() != null);
        }
    }

    @Test
    public void desDecryptReachesMalformedBase64DecodeBeforeCipherFailure() {
        DesConfig config = new DesConfig();
        config.Algorithms = DesAlgorithms.DES_CBC_PKCS5Padding;
        config.Key = "12345678".getBytes(StandardCharsets.UTF_8);
        config.IV = "12345678".getBytes(StandardCharsets.UTF_8);
        config.OutFormat = OutFormat.Base64;

        DesUtil util = new DesUtil();
        util.setConfig(config);

        try {
            util.decrypt("AB==");
            fail("Expected block cipher decryption to fail after malformed Base64 was decoded.");
        } catch (RuntimeException expected) {
            assertArrayEquals(new byte[]{0}, Utils.base64("AB=="));
        }
    }

    @Test
    public void sm4DecryptEvaluatesMalformedBase64BeforeMissingCryptoFailure() {
        SM4Util util = new SM4Util();

        try {
            util.decrypt("AB==");
            fail("Expected decrypt to fail after evaluating the malformed Base64 argument.");
        } catch (NullPointerException expected) {
            assertArrayEquals(new byte[]{0}, Utils.base64("AB=="));
        }
    }

    @Test
    public void zucDecryptEvaluatesMalformedBase64BeforeMissingCryptoFailure() {
        ZUCUtil util = new ZUCUtil();

        try {
            util.decrypt("AB==");
            fail("Expected decrypt to fail after evaluating the malformed Base64 argument.");
        } catch (NullPointerException expected) {
            assertArrayEquals(new byte[]{0}, Utils.base64("AB=="));
        }
    }
}
