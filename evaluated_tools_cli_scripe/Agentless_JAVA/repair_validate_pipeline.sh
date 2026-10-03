#!/usr/bin/env bash
set -e
set -o pipefail
set -u

# ===== Argument Parsing =====
TARGET_ID=""

for arg in "$@"; do
  case $arg in
    --target_id=*)
      TARGET_ID="${arg#*=}"
      shift
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 --target_id=<TARGET_ID>"
      exit 1
      ;;
  esac
done

# ===== Argument Validation =====
if [ -z "$TARGET_ID" ]; then
  echo "Error: --target_id is required"
  echo "Usage: $0 --target_id=<TARGET_ID>"
  exit 1
fi

echo "=========================================="
echo "Running repair & validation pipeline"
echo "TARGET_ID = ${TARGET_ID}"
echo "=========================================="

# =========================================================
# 5. Repair
# =========================================================
echo "[5] Repair generation"

for i in {0..3}; do
  echo "  -> Repair round $i"
  python agentless/repair/repair_java_local.py \
    --loc_file results/poc-bench-lite/edit_location_individual/loc_merged_${i}-${i}_outputs.jsonl \
    --output_folder results/poc-bench-lite/repair_sample_$((i+1)) \
    --loc_interval \
    --top_n 3 \
    --context_window 10 \
    --max_samples 10 \
    --cot \
    --diff_format \
    --gen_and_process \
    --num_threads 2 \
    --target_id "${TARGET_ID}"
done

# =========================================================
# 6. Convert repair outputs to patch format
# =========================================================
echo "[6] Convert repair outputs to patch format"

python agentless/validate/jsonl2patch_bench.py \
  --target_id "${TARGET_ID}"

# =========================================================
# 7.1 Deduplicate patches
# =========================================================
echo "[7.1] Deduplicate patches"

python agentless/validate/dedup_patch.py \
  --input results/poc-bench-lite/repair_patch \
  --output results/poc-bench-lite/repair_diff_patch

echo "=========================================="
echo "Repair & validation pipeline finished"
echo "=========================================="

# =========================================================
# 8. Copy patch to Docker and organize results
# =========================================================

RESULT_ROOT="results"
SRC_DIR="${RESULT_ROOT}/poc-bench-lite"
DST_PARENT="${RESULT_ROOT}/agentless-19issue"
DST_DIR="${DST_PARENT}/${TARGET_ID}"

CONTAINER_ID="9a401de53fa9"
CONTAINER_DST="/VESTA/resource/agentless_patch/${TARGET_ID}"

echo "[8.1] Copy deduplicated patches into Docker container (before mv)"

docker exec "${CONTAINER_ID}" mkdir -p "${CONTAINER_DST}"

docker cp \
  "${SRC_DIR}/repair_diff_patch/." \
  "${CONTAINER_ID}:${CONTAINER_DST}"

echo "[8.2] Move poc-bench-lite → agentless-19issue/${TARGET_ID}"

mkdir -p "${DST_PARENT}"
mv "${SRC_DIR}" "${DST_DIR}"

