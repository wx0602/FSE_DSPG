#passing CVE-Number, 
export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/TEXT-215/geoportal-server/geoportal
$PYTHON /VESTA/vesta/VESTA.py TEXT-215 geoportal-server/geoportal geoportal-server/geoportal "org.apache.commons.text.translate.OctalUnescaper:translate(java.lang.CharSequence,java.io.Writer)" geoportal.jar manual