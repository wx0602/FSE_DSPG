# Vulnerability Fix Task: LANG-1385_ewallet

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

A proof-of-concept (PoC) is provided at the end of this issue. Use it as a concrete reference to understand how the vulnerability is triggered, trace the affected downstream code path, and validate your repair. Do not hard-code a fix only for the exact PoC input; address the underlying vulnerability while preserving intended functionality.

## Vulnerability ID

`LANG-1385_ewallet`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
Description

Test case:
NumberUtils.createNumber("L")
Expected: NumberFormatException
Got:
java.lang.StringIndexOutOfBoundsException: String index out of range: 0
at java.lang.String.charAt(String.java:658)
at org.apache.commons.lang3.math.NumberUtils.createNumber(NumberUtils.java:528)

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

fix this vulnerability. Even if the fix fails, you must still modify the code in the best possible way.

## Proof of Concept (PoC) Reference

The following PoC demonstrates a known way to exercise the vulnerable behavior in this project. Treat it as repair and validation guidance; inspect the surrounding implementation and related input variants as well.

```java
// ------------------------------------------------------------------------------------------------
// Source: wallet-base/src/test/java/com/fr/chain/utils/NumberUtil_ESTest.java
// ------------------------------------------------------------------------------------------------

package com.fr.chain.utils;

import org.junit.Test;

import static org.junit.Assert.fail;

public class NumberUtil_ESTest {

    @Test
    public void numberUtil_createNumber_L_shouldThrowNumberFormatException_in_fixed_version() {
        try {
            // �� wallet-base �Լ����߼���
            // NumberUtil.createNumber -> org.apache.commons.lang3.math.NumberUtils.createNumber
            NumberUtil.createNumber("L");

            fail("Expected NumberFormatException");
        } catch (NumberFormatException expected) {
            // �޸��汾(>=3.8)��Ӧ�� NumberFormatException => ����ͨ��
        }
    }
}
```
