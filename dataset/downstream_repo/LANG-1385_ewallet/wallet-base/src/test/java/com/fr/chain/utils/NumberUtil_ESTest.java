package com.fr.chain.utils;

import org.junit.Test;

import static org.junit.Assert.fail;

public class NumberUtil_ESTest {

    @Test
    public void numberUtil_createNumber_L_shouldThrowNumberFormatException_in_fixed_version() {
        try {
            // 走 wallet-base 自己的逻辑：
            // NumberUtil.createNumber -> org.apache.commons.lang3.math.NumberUtils.createNumber
            NumberUtil.createNumber("L");

            fail("Expected NumberFormatException");
        } catch (NumberFormatException expected) {
            // 修复版本(>=3.8)：应抛 NumberFormatException => 测试通过
        }
    }
}
