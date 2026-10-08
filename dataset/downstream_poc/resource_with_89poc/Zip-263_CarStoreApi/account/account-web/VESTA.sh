export PYTHON=/usr/bin/python3
export EVOSUITE="java -jar /VESTA/code/generator/master/target/evosuite-master-1.1.1-SNAPSHOT.jar -Dsandbox=false"
export NOW_DIR=/VESTA/resource/Zip-263/CarStoreApi/account/account-web
$PYTHON /VESTA/vesta/VESTA.py Zip-263 CarStoreApi account/account-web "net.lingala.zip4j.ZipFile:<init>(java.io.File)" account.jar manual