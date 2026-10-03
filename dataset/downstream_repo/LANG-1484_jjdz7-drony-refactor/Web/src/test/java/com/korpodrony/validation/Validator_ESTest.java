package com.korpodrony.validation;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class Validator_ESTest {

    @Test
    void lang1484_repro_through_client_validator() {
        Validator validator = new Validator();

        // 证明输入在 Java 标准解析里是合法的（核心基准依据）
        assertDoesNotThrow(() -> Double.parseDouble("100."));

        // 直接获取下游 Validator 的结果，消除上游依赖
        boolean validatorResult = validator.validateInteger("100.");

        // 核心判据：验证下游 Validator 应返回 true，若返回 false 则为下游 bug
        assertTrue(validatorResult,
                "Expected validateInteger(\"100.\") to be true (trailing dot should be accepted). " +
                "If it is false, you are observing the LANG-1484 behavior (downstream Validator bug).");
    }
}

