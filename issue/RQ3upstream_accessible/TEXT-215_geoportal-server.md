# Vulnerability Fix Task: TEXT-215_geoportal-server

## Prompt

You are working on the target project associated with this vulnerability. Your task is to fix or mitigate the vulnerability described below.

You must inspect the codebase, identify where the vulnerable dependency or vulnerable behavior is used, and apply the best possible mitigation without upgrading the vulnerable library version.

The upstream source repository of the vulnerable third-party library is located at `TEXT-215/` under the workspace root.

The `TEXT-215/` subdirectory is read-only. Do not create, modify, rename, or delete any files in it.

## Vulnerability ID

`TEXT-215_geoportal-server`

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
