#!/bin/bash
set -euo pipefail

# ====================== 1. Initialize Variables and Parse Arguments ======================
TARGET_ID=""
BUGGY=""

# Parse command line arguments
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

# Check required parameters
if [[ -z "$TARGET_ID" || -z "$BUGGY" ]]; then
  echo "ERROR: --target_id and --buggy are required!"
  echo "Example: $0 --target_id=12345 --buggy=true"
  exit 1
fi

echo "===== Starting execution with parameters: target_id=$TARGET_ID, buggy=$BUGGY ====="

# ====================== 2. Execute Steps ======================
# Step 1: Run repo_joern_local_cli.py
echo "[Step 1] Running python src/repo_joern_local_cli.py --target_id=$TARGET_ID"
python src/repo_joern_local_cli.py --target_id="$TARGET_ID"

# Step 2: Rename target_id folder under workspace
echo "[Step 2] Renaming ./workspace/$TARGET_ID to ${TARGET_ID}_buggy"
WORKSPACE_DIR="./workspace/$TARGET_ID"
if [[ -d "$WORKSPACE_DIR" ]]; then
  mv "$WORKSPACE_DIR" "./workspace/${TARGET_ID}_buggy"
  echo "Folder rename completed"
else
  echo "WARNING: Folder $WORKSPACE_DIR does not exist, skipping rename"
fi

# Step 3: Run pro_dataset.py
echo "[Step 3] Running dataset_cin/pro_dataset.py"
python dataset_cin/pro_dataset.py \
  --repo="./VESTA_resource/resource_checkout/$TARGET_ID" \
  --buggy="$BUGGY" \
  --out=./out.json

# Step 4: Run react_sf_gen_patch_local_cli.py
echo "[Step 4] Running src/agent/react_sf_gen_patch_local_cli.py --target_id=$TARGET_ID"
python src/agent/react_sf_gen_patch_local_cli.py --target_id="$TARGET_ID"

# Step 5: Run json2patch.py
echo "[Step 5] Running src/patch_validation/json2patch.py"
python3 src/patch_validation/json2patch.py \
  --input_dataset="./Reinfix/reinfix/out.json" \
  --target_id="$TARGET_ID" \
  --input_patchs="./Reinfix/output/sf_patches/${TARGET_ID}.json" \
  --output_patchs="./Reinfix/output/generated_patch_files/$TARGET_ID" \
  --input_repo="./VESTA_resource/resource_checkout/$TARGET_ID"

# Step 6: Copy files to docker container
echo "[Step 6] Copying patch files to docker container 9a401de53fa9"
PATCH_SRC_DIR="./Reinfix/output/generated_patch_files/$TARGET_ID"
DOCKER_DEST="9a401de53fa9:/VESTA/resource/reinfix/reinfix_patch/"

# Check if source folder exists
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

# ====================== 3. Execution Completed ======================
echo "===== All steps completed! target_id=$TARGET_ID ====="
exit 0

