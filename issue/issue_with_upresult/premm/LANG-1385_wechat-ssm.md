# Vulnerability Fix Task: LANG-1385_wechat-ssm

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`LANG-1385_wechat-ssm`

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

## Untrusted Upstream Patch Reference

The following patch was generated for the upstream library and is provided only as a potentially useful reference. It is **not verified ground truth** and may be correct, partially correct, incorrect, incomplete, unsafe, or inapplicable to this downstream project. Do not assume that it fixes the vulnerability, and do not apply or copy it blindly.

Independently inspect the downstream codebase and understand how the vulnerability is manifested there. Use the reference patch to identify the intended security fix and adapt the relevant changes to the downstream implementation. Do not assume that the reference patch can be applied directly; it may require modification due to differences in code structure, APIs, or dependency versions. Reject or replace parts of the patch when they are not applicable to the downstream project, and implement the best possible downstream fix. The final output should be a code change/patch applied to the downstream project.

```diff
--- a/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
+++ b/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
@@ -448,181 +448,183 @@
      * @return Number created from the string (or null if the input is null)
      * @throws NumberFormatException if the value cannot be converted
      */
-    public static Number createNumber(final String str) throws NumberFormatException {
-        if (str == null) {
-            return null;
-        }
-        if (StringUtils.isBlank(str)) {
-            throw new NumberFormatException("A blank string is not a valid number");
-        }
-        // Need to deal with all possible hex prefixes here
-        final String[] hex_prefixes = {"0x", "0X", "-0x", "-0X", "#", "-#"};
-        int pfxLen = 0;
-        for(final String pfx : hex_prefixes) {
-            if (str.startsWith(pfx)) {
-                pfxLen += pfx.length();
+public static Number createNumber(final String str) throws NumberFormatException {
+    if (str == null) {
+        return null;
+    }
+    if (StringUtils.isBlank(str)) {
+        throw new NumberFormatException("A blank string is not a valid number");
+    }
+    // Need to deal with all possible hex prefixes here
+    final String[] hex_prefixes = {"0x", "0X", "-0x", "-0X", "#", "-#"};
+    int pfxLen = 0;
+    for(final String pfx : hex_prefixes) {
+        if (str.startsWith(pfx)) {
+            pfxLen += pfx.length();
+            break;
+        }
+    }
+    if (pfxLen > 0) { // we have a hex number
+        char firstSigDigit = 0; // strip leading zeroes
+        for(int i = pfxLen; i < str.length(); i++) {
+            firstSigDigit = str.charAt(i);
+            if (firstSigDigit == '0') { // count leading zeroes
+                pfxLen++;
+            } else {
                 break;
             }
         }
-        if (pfxLen > 0) { // we have a hex number
-            char firstSigDigit = 0; // strip leading zeroes
-            for(int i = pfxLen; i < str.length(); i++) {
-                firstSigDigit = str.charAt(i);
-                if (firstSigDigit == '0') { // count leading zeroes
-                    pfxLen++;
-                } else {
-                    break;
-                }
-            }
-            final int hexDigits = str.length() - pfxLen;
-            if (hexDigits > 16 || (hexDigits == 16 && firstSigDigit > '7')) { // too many for Long
-                return createBigInteger(str);
-            }
-            if (hexDigits > 8 || (hexDigits == 8 && firstSigDigit > '7')) { // too many for an int
-                return createLong(str);
-            }
-            return createInteger(str);
-        }
-        final char lastChar = str.charAt(str.length() - 1);
-        String mant;
-        String dec;
-        String exp;
-        final int decPos = str.indexOf('.');
-        final int expPos = str.indexOf('e') + str.indexOf('E') + 1; // assumes both not present
-        // if both e and E are present, this is caught by the checks on expPos (which prevent IOOBE)
-        // and the parsing which will detect if e or E appear in a number due to using the wrong offset
-
-        int numDecimals = 0; // Check required precision (LANG-693)
-        if (decPos > -1) { // there is a decimal point
-
-            if (expPos > -1) { // there is an exponent
-                if (expPos < decPos || expPos > str.length()) { // prevents double exponent causing IOOBE
+        final int hexDigits = str.length() - pfxLen;
+        if (hexDigits > 16 || (hexDigits == 16 && firstSigDigit > '7')) { // too many for Long
+            return createBigInteger(str);
+        }
+        if (hexDigits > 8 || (hexDigits == 8 && firstSigDigit > '7')) { // too many for an int
+            return createLong(str);
+        }
+        return createInteger(str);
+    }
+    final char lastChar = str.charAt(str.length() - 1);
+    String mant;
+    String dec;
+    String exp;
+    final int decPos = str.indexOf('.');
+    final int expPos = str.indexOf('e') + str.indexOf('E') + 1; // assumes both not present
+    // if both e and E are present, this is caught by the checks on expPos (which prevent IOOBE)
+    // and the parsing which will detect if e or E appear in a number due to using the wrong offset
+
+    int numDecimals = 0; // Check required precision (LANG-693)
+    if (decPos > -1) { // there is a decimal point
+
+        if (expPos > -1) { // there is an exponent
+            if (expPos < decPos || expPos > str.length()) { // prevents double exponent causing IOOBE
+                throw new NumberFormatException(str + " is not a valid number.");
+            }
+            dec = str.substring(decPos + 1, expPos);
+        } else {
+            dec = str.substring(decPos + 1);
+        }
+        mant = getMantissa(str, decPos);
+        numDecimals = dec.length(); // gets number of digits past the decimal to ensure no loss of precision for floating point numbers.
+    } else {
+        if (expPos > -1) {
+            if (expPos > str.length()) { // prevents double exponent causing IOOBE
+                throw new NumberFormatException(str + " is not a valid number.");
+            }
+            mant = getMantissa(str, expPos);
+        } else {
+            mant = getMantissa(str);
+        }
+        dec = null;
+    }
+    if (!Character.isDigit(lastChar) && lastChar != '.') {
+        if (expPos > -1 && expPos < str.length() - 1) {
+            exp = str.substring(expPos + 1, str.length() - 1);
+        } else {
+            exp = null;
+        }
+        //Requesting a specific type..
+        final String numeric = str.substring(0, str.length() - 1);
+        final boolean allZeros = isAllZeros(mant) && isAllZeros(exp);
+        switch (lastChar) {
+            case 'l' :
+            case 'L' :
+                if (numeric.length() == 0) {
                     throw new NumberFormatException(str + " is not a valid number.");
                 }
-                dec = str.substring(decPos + 1, expPos);
-            } else {
-                dec = str.substring(decPos + 1);
-            }
-            mant = getMantissa(str, decPos);
-            numDecimals = dec.length(); // gets number of digits past the decimal to ensure no loss of precision for floating point numbers.
-        } else {
-            if (expPos > -1) {
-                if (expPos > str.length()) { // prevents double exponent causing IOOBE
-                    throw new NumberFormatException(str + " is not a valid number.");
+                if (dec == null
+                    && exp == null
+                    && (numeric.charAt(0) == '-' && isDigits(numeric.substring(1)) || isDigits(numeric))) {
+                    try {
+                        return createLong(numeric);
+                    } catch (final NumberFormatException nfe) { // NOPMD
+                        // Too big for a long
+                    }
+                    return createBigInteger(numeric);
+
                 }
-                mant = getMantissa(str, expPos);
-            } else {
-                mant = getMantissa(str);
-            }
-            dec = null;
-        }
-        if (!Character.isDigit(lastChar) && lastChar != '.') {
-            if (expPos > -1 && expPos < str.length() - 1) {
-                exp = str.substring(expPos + 1, str.length() - 1);
-            } else {
-                exp = null;
-            }
-            //Requesting a specific type..
-            final String numeric = str.substring(0, str.length() - 1);
-            final boolean allZeros = isAllZeros(mant) && isAllZeros(exp);
-            switch (lastChar) {
-                case 'l' :
-                case 'L' :
-                    if (dec == null
-                        && exp == null
-                        && (numeric.charAt(0) == '-' && isDigits(numeric.substring(1)) || isDigits(numeric))) {
-                        try {
-                            return createLong(numeric);
-                        } catch (final NumberFormatException nfe) { // NOPMD
-                            // Too big for a long
-                        }
-                        return createBigInteger(numeric);
-
+                throw new NumberFormatException(str + " is not a valid number.");
+            case 'f' :
+            case 'F' :
+                try {
+                    final Float f = NumberUtils.createFloat(numeric);
+                    if (!(f.isInfinite() || (f.floatValue() == 0.0F && !allZeros))) {
+                        //If it's too big for a float or the float value = 0 and the string
+                        //has non-zeros in it, then float does not have the precision we want
+                        return f;
                     }
-                    throw new NumberFormatException(str + " is not a valid number.");
-                case 'f' :
-                case 'F' :
-                    try {
-                        final Float f = NumberUtils.createFloat(numeric);
-                        if (!(f.isInfinite() || (f.floatValue() == 0.0F && !allZeros))) {
-                            //If it's too big for a float or the float value = 0 and the string
-                            //has non-zeros in it, then float does not have the precision we want
-                            return f;
-                        }
-
-                    } catch (final NumberFormatException nfe) { // NOPMD
-                        // ignore the bad number
+
+                } catch (final NumberFormatException nfe) { // NOPMD
+                    // ignore the bad number
+                }
+                //$FALL-THROUGH$
+            case 'd' :
+            case 'D' :
+                try {
+                    final Double d = NumberUtils.createDouble(numeric);
+                    if (!(d.isInfinite() || (d.floatValue() == 0.0D && !allZeros))) {
+                        return d;
                     }
-                    //$FALL-THROUGH$
-                case 'd' :
-                case 'D' :
-                    try {
-                        final Double d = NumberUtils.createDouble(numeric);
-                        if (!(d.isInfinite() || (d.floatValue() == 0.0D && !allZeros))) {
-                            return d;
-                        }
-                    } catch (final NumberFormatException nfe) { // NOPMD
-                        // ignore the bad number
-                    }
-                    try {
-                        return createBigDecimal(numeric);
-                    } catch (final NumberFormatException e) { // NOPMD
-                        // ignore the bad number
-                    }
-                    //$FALL-THROUGH$
-                default :
-                    throw new NumberFormatException(str + " is not a valid number.");
-
-            }
-        }
-        //User doesn't have a preference on the return type, so let's start
-        //small and go from there...
-        if (expPos > -1 && expPos < str.length() - 1) {
-            exp = str.substring(expPos + 1, str.length());
-        } else {
-            exp = null;
-        }
-        if (dec == null && exp == null) { // no decimal point and no exponent
-            //Must be an Integer, Long, Biginteger
-            try {
-                return createInteger(str);
-            } catch (final NumberFormatException nfe) { // NOPMD
-                // ignore the bad number
-            }
-            try {
-                return createLong(str);
-            } catch (final NumberFormatException nfe) { // NOPMD
-                // ignore the bad number
-            }
-            return createBigInteger(str);
-        }
-
-        //Must be a Float, Double, BigDecimal
-        final boolean allZeros = isAllZeros(mant) && isAllZeros(exp);
+                } catch (final NumberFormatException nfe) { // NOPMD
+                    // ignore the bad number
+                }
+                try {
+                    return createBigDecimal(numeric);
+                } catch (final NumberFormatException e) { // NOPMD
+                    // ignore the bad number
+                }
+                //$FALL-THROUGH$
+            default :
+                throw new NumberFormatException(str + " is not a valid number.");
+
+        }
+    }
+    //User doesn't have a preference on the return type, so let's start
+    //small and go from there...
+    if (expPos > -1 && expPos < str.length() - 1) {
+        exp = str.substring(expPos + 1, str.length());
+    } else {
+        exp = null;
+    }
+    if (dec == null && exp == null) { // no decimal point and no exponent
+        //Must be an Integer, Long, Biginteger
         try {
-            if(numDecimals <= 7){// If number has 7 or fewer digits past the decimal point then make it a float
-                final Float f = createFloat(str);
-                if (!(f.isInfinite() || (f.floatValue() == 0.0F && !allZeros))) {
-                    return f;
-                }
-            }
+            return createInteger(str);
         } catch (final NumberFormatException nfe) { // NOPMD
             // ignore the bad number
         }
         try {
-            if(numDecimals <= 16){// If number has between 8 and 16 digits past the decimal point then make it a double
-                final Double d = createDouble(str);
-                if (!(d.isInfinite() || (d.doubleValue() == 0.0D && !allZeros))) {
-                    return d;
-                }
-            }
+            return createLong(str);
         } catch (final NumberFormatException nfe) { // NOPMD
             // ignore the bad number
         }
-
-        return createBigDecimal(str);
-    }
-
+        return createBigInteger(str);
+    }
+
+    //Must be a Float, Double, BigDecimal
+    final boolean allZeros = isAllZeros(mant) && isAllZeros(exp);
+    try {
+        if(numDecimals <= 7){// If number has 7 or fewer digits past the decimal point then make it a float
+            final Float f = createFloat(str);
+            if (!(f.isInfinite() || (f.floatValue() == 0.0F && !allZeros))) {
+                return f;
+            }
+        }
+    } catch (final NumberFormatException nfe) { // NOPMD
+        // ignore the bad number
+    }
+    try {
+        if(numDecimals <= 16){// If number has between 8 and 16 digits past the decimal point then make it a double
+            final Double d = createDouble(str);
+            if (!(d.isInfinite() || (d.doubleValue() == 0.0D && !allZeros))) {
+                return d;
+            }
+        }
+    } catch (final NumberFormatException nfe) { // NOPMD
+        // ignore the bad number
+    }
+
+    return createBigDecimal(str);
+}
     /**
      * <p>Utility method for {@link #createNumber(java.lang.String)}.</p>
      *
```

Fix this vulnerability in the downstream project. Even if the fix is incomplete or tests fail, you must still modify the code in the best possible way.
