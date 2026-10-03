#!/bin/bash
file_path=../App/src/main/resources/META-INF/persistence.xml
orginal=$(sed '16q;d' $file_path)
new="            <property name=\"javax.persistence.jdbc.password\" value=\""password"\"/>"
sed -i "s|$orginal|$new|g" $file_path