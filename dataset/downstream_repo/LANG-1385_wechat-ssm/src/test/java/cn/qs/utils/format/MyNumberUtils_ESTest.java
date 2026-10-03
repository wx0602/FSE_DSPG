package cn.qs.utils.format;

import org.junit.Test;

import static org.junit.Assert.fail;

public class MyNumberUtils_ESTest{

  @Test
  public void toFixedDecimal_shouldThrowNumberFormatException_for_L() {
    try {
      // ÕâÐÐ»á×ßµ½£ºMyNumberUtils -> NumberUtils.createNumber("L")
      // ÐÞ¸´°æ±¾(>=3.8)£ºÓ¦Å× NumberFormatException => ±» catch => ²âÊÔÍ¨¹ý
      // Â©¶´°æ±¾(Èç 3.7)£º»áÅ× StringIndexOutOfBoundsException => Î´±» catch => ²âÊÔÊ§°Ü£¨´¥·¢ LANG-1385£©
      MyNumberUtils.toFixedDecimal("L", 2);

      fail("Expected NumberFormatException");
    } catch (NumberFormatException expected) {
      // ÐÞ¸´°æ±¾Í¨¹ý
    }
  }

  @Test
  public void toFixedDecimalWithPercent_shouldThrowNumberFormatException_for_L() {
    try {
      MyNumberUtils.toFixedDecimalWithPercent("L", 2);
      fail("Expected NumberFormatException");
    } catch (NumberFormatException expected) {
      // ÐÞ¸´°æ±¾Í¨¹ý
    }
  }
}
