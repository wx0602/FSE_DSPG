export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.0.6.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/Zip-263/ZingClient
$PYTHON /VESTA/vesta/VESTA.py Zip-263 ZingClient ZingClient "net.lingala.zip4j.ZipFile:<init>(java.io.File)" ZingClient-1.0-SNAPSHOT.jar manual