# Vulnerability Fix Task: TEXT-215_geoportal-esri

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

## Vulnerability ID

`TEXT-215_geoportal-esri`

## CVE / Issue Description

The current project depends on a vulnerable version of the third-party library mentioned in the title. The specific vulnerability details on NVD are as follows:
Description:
A security breach can be used in the NumericEntityUnescaper through the use of decimal character entities.
At line 117 a string of hexadecimal characters are searched, whether or not the entity is an hexadecimal one.
Therefore, if the "semiColonOptional" option is enabled and a deicmal entity without semi-colon is immediately followed by one or several letters from A to F, these letters will be caught. The Integer parsing with a radix at 10 will then fail and the whole entity will be ignored.
Example:
If one uses the following string: 
<iframe src=\"&#106avascript:alert(1)\">
The sequence identifying the entity will wrongly be "&#106a" instead of "&#106".
As "&#106a" is not a valid decimal entity, its Integer parsing fails and the whole entity remains escaped.
Such code would then trigger the alert on all modern browsers.
Solution:
The fix for this is to restrict hexadecimal characters to hexadecimal entities and decimal characters to decimal entities.

## Additional Vulnerability Information

N/A

## Mandatory Fix Constraint

When fixing this vulnerability, please do not upgrade the library version. Instead, use mitigation measures to address the issue. These measures may include, but are not limited to: disabling the affected functionality, manually patching the vulnerable code, restricting access to the vulnerable components, enhancing monitoring and logging, or finding a secure alternative solution. Ensure that the security risk is minimized and system stability is maintained without changing the library version.

fix this vulnerability. Even if the fix fails, you must still modify the code in the best possible way.

## Vulnerability Call Chain Guidance

The following call chains identify likely entry points and propagation paths related to the vulnerability. Treat them as important guidance for the repair: carefully inspect the listed methods and classes, verify how the vulnerable behavior or data flows through these paths, and prioritize chain-related code during root-cause analysis and patch development. The chains may not capture every relevant path, so also consider additional code when supported by the source code and tests. You may deviate from the chains when there is clear technical evidence that a different repair location or approach is more appropriate.

```text
Public Method 1
Method: <com.esri.geoportal.base.util.Val: java.lang.String unescape(java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>
2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeOctal(java.lang.String)>
3. <com.esri.geoportal.base.util.Val: java.lang.String unescape(java.lang.String)>

Public Method 2
Method: <com.esri.geoportal.base.util.Val: java.lang.String unescapeNunmericEntity(java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>
2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeNunmericEntity(java.lang.String)>

Public Method 3
Method: <com.esri.geoportal.base.util.Val: java.lang.String unescapeOctalToUnicode(java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>
2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeOctalToUnicode(java.lang.String)>

Public Method 4
Method: <com.esri.geoportal.base.util.Val: java.lang.String unescapeUnicode(java.lang.String)>
Shortest reverse path from source:
1. <org.apache.commons.text.translate.CharSequenceTranslator: void translate(java.lang.CharSequence,java.io.Writer)>
2. <com.esri.geoportal.base.util.Val: java.lang.String unescapeUnicode(java.lang.String)>
```
