export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/LANG-1385/wechat-ssm
$PYTHON /VESTA/vesta/VESTA.py LANG-1385 wechat-ssm wechat-ssm "org.apache.commons.lang3.math.NumberUtils:createNumber(java.lang.String)" springboot-ssm-0.0.1-SNAPSHOT.jar StringIndexOutOfBoundsException