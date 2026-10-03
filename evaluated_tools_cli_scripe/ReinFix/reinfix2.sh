#!/bin/bash
set -euo pipefail  


TARGET_ID=""
BUGGY=""


for arg in "$@"; do
  case $arg in
    --target_id=*)
      TARGET_ID="${arg#*=}"  
      shift  
      ;;
    --buggy=*)
      BUGGY="${arg#*=}"
      shift
      ;;
    *)
      
      echo "ERROR: Unknown argument $arg"
      echo "Usage: $0 --target_id=<TARGET_ID> --buggy=<BUGGY_VALUE>"
      exit 1
      ;;
  esac
done


if [[ -z "$TARGET_ID" || -z "$BUGGY" ]]; then
  echo "ERROR: --target_id and --buggy are required!"
  echo "Example: $0 --target_id=12345 --buggy=true"
  exit 1
fi

echo "===== Starting workflow with parameters: target_id=$TARGET_ID, buggy=$BUGGY ====="

echo "[Step 6] Copying patch files to docker container 9a401de53fa9"
PATCH_SRC_DIR="./Reinfix/output/generated_patch_files/$TARGET_ID"

DOCKER_DEST="9a401de53fa9:/VESTA/resource/reinfix/reinfix_patch/"


if [[ -d $PATCH_SRC_DIR ]]; then  

  echo $PATCH_SRC_DIR  
  echo $DOCKER_DEST/   

  echo "Running command: docker exec 9a401de53fa9 mkdir -p /VESTA/resource/reinfix/reinfix_patch/$TARGET_ID"
  
  docker exec 9a401de53fa9 mkdir -p /VESTA/resource/reinfix/reinfix_patch/$TARGET_ID
  
  echo "Running command: docker cp $PATCH_SRC_DIR $DOCKER_DEST"
  
  docker cp $PATCH_SRC_DIR $DOCKER_DEST
  echo "Folder copy completed"
else
  echo "ERROR: Source folder $PATCH_SRC_DIR does not exist, cannot run docker cp"
  exit 1
fi

echo "===== All steps completed! target_id=$TARGET_ID ====="
exit 0

