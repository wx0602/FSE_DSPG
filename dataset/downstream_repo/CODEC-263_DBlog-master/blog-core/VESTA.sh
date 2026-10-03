export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/CODEC-263/DBlog-master/blog-core
$PYTHON /VESTA/vesta/VESTA.py CODEC-263 DBlog-master blog-core "org.apache.commons.codec.binary.Base64:decodeBase64(java.lang.String)" blog-core.jar valid