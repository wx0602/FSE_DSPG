export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/CODEC-270/BurpCrypto-master
$PYTHON /VESTA/vesta/VESTA.py CODEC-270 BurpCrypto-master BurpCrypto-master "org.apache.commons.codec.binary.Base64:decodeBase64(java.lang.String)" BurpCrypto-0.1.9.1.jar valid