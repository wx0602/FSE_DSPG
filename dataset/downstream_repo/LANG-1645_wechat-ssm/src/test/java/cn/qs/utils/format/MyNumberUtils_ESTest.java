//
// Source code recreated from a .class file by IntelliJ IDEA
// (powered by FernFlower decompiler)
//

package cn.qs.utils.format;

import java.math.BigInteger;
import org.apache.commons.lang3.math.NumberUtils;
import org.junit.Test;

public class MyNumberUtils_ESTest {
    public MyNumberUtils_ESTest() {
    }

    @Test(
        timeout = 4000L
    )
    public void test00() throws Throwable {
        long long0 = NumberUtils.toLong("");
        byte var5 = 0;
        String var4 = "";
        Object var3 = null;
        String var6 = null;
        var4 = "+0xF";
        var6 = MyNumberUtils.toFixedDecimal(var4, var5);
    }

    @Test(
        timeout = 4000L
    )
    public void test01() throws Throwable {
        long long0 = NumberUtils.toLong((String)null, 1L);
        MyNumberUtils.toFixedDecimal("", 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test02() throws Throwable {
        long long0 = NumberUtils.toLong("", 1L);
        MyNumberUtils.toFixedDecimal("", 3);
    }

    @Test(
        timeout = 4000L
    )
    public void test03() throws Throwable {
        String[] stringArray0 = new String[3];
        MyNumberUtils.main(stringArray0);
        BigInteger bigInteger0 = NumberUtils.createBigInteger((String)null);
        MyNumberUtils.toFixedDecimal((String)null, -1);
    }

    @Test(
        timeout = 4000L
    )
    public void test04() throws Throwable {
        Long long0 = new Long(-1L);
        String string0 = MyNumberUtils.toFixedDecimalWithPercent(long0, 0);
        int int0 = NumberUtils.toInt("-100%", 0);
        String string1 = MyNumberUtils.toFixedDecimalWithPercent(0, 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test05() throws Throwable {
        long long0 = NumberUtils.max(-1L, -1L, 0L);
        MyNumberUtils.toFixedDecimal("", -1);
    }

    @Test(
        timeout = 4000L
    )
    public void test06() throws Throwable {
        long long0 = NumberUtils.max(-1L, 0L, 0L);
        MyNumberUtils.toFixedDecimal("", -1);
    }

    @Test(
        timeout = 4000L
    )
    public void test07() throws Throwable {
        long long0 = NumberUtils.max(0L, 0L, 0L);
        MyNumberUtils.toFixedDecimal("", -1);
    }

    @Test(
        timeout = 4000L
    )
    public void test08() throws Throwable {
        byte byte0 = NumberUtils.toByte((String)null);
        MyNumberUtils.toFixedDecimal((String)null, 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test09() throws Throwable {
        String[] stringArray0 = new String[]{null, "", "", null, ""};
        MyNumberUtils.main(stringArray0);
        new MyNumberUtils();
        byte byte0 = NumberUtils.toByte("WxWk`4_(d(DEu1'{P");
        Long long0 = NumberUtils.createLong(stringArray0[3]);
        MyNumberUtils.toFixedDecimal("", 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test10() throws Throwable {
        String[] stringArray0 = new String[]{"", "", null};
        MyNumberUtils.main(stringArray0);
        MyNumberUtils.toFixedDecimal("", 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test13() throws Throwable {
        String[] stringArray0 = new String[1];
        MyNumberUtils.main(stringArray0);
        int int0 = NumberUtils.compare(-1L, 1L);
        Double double0 = NumberUtils.DOUBLE_ZERO;
        String string0 = MyNumberUtils.toFixedDecimal(double0, -1);
    }

    @Test(
        timeout = 4000L
    )
    public void test14() throws Throwable {
        String[] stringArray0 = new String[0];
        MyNumberUtils.main(stringArray0);
        int int0 = NumberUtils.compare(0L, 0L);
        Double double0 = NumberUtils.DOUBLE_ZERO;
        String string0 = MyNumberUtils.toFixedDecimal(double0, 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test16() throws Throwable {
        byte byte0 = NumberUtils.toByte("");
        MyNumberUtils.toFixedDecimal("", 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test17() throws Throwable {
        MyNumberUtils.toFixedDecimal("", 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test18() throws Throwable {
        Double double0 = NumberUtils.DOUBLE_ONE;
        String string0 = MyNumberUtils.toFixedDecimal(double0, 2);
    }

    @Test(
        timeout = 4000L
    )
    public void test19() throws Throwable {
        new MyNumberUtils();
        Long long0 = NumberUtils.LONG_ONE;
        String string0 = MyNumberUtils.toFixedDecimalWithPercent(long0, 0);
    }

    @Test(
        timeout = 4000L
    )
    public void test20() throws Throwable {
        MyNumberUtils.toFixedDecimalWithPercent("cn.qs.utils.format.MyNumberUtils", 0);
    }
}

