export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/IO-611/velocity-engine/velocity-engine-core
$PYTHON /VESTA/vesta/VESTA.py IO-611 velocity-engine velocity-engine-core "org.apache.velocity.shaded.commons.io.FilenameUtils:normalize(java.lang.String,boolean)" velocity-engine-core-2.2-SNAPSHOT.jar //foo//bar