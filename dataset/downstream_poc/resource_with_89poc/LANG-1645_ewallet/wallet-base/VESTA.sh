export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/LANG-1645/ewallet/wallet-base
$PYTHON /VESTA/vesta/VESTA.py LANG-1645 ewallet wallet-base "org.apache.commons.lang3.math.NumberUtils:createNumber(java.lang.String)" wallet-base-0.0.1-SNAPSHOT.jar NumberFormatException