export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar  -Dsandbox=false"
export NOW_DIR=/VESTA/resource/LANG-1484/jjdz7-drony-refactor/Web
$PYTHON /VESTA/vesta/VESTA.py LANG-1484 jjdz7-drony-refactor Web "org.apache.commons.lang3.math.NumberUtils:isParsable(java.lang.String)" LibrisWeb.war manual