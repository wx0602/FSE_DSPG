#!/usr/bin/env bash
set -e


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


if [ -z "$TARGET_ID" ]; then
  echo "Error: --target_id is required"
  echo "Usage: $0 --target_id=<TARGET_ID>"
  exit 1
fi

echo "=========================================="
echo "Running localization pipeline"
echo "TARGET_ID = ${TARGET_ID}"
echo "=========================================="


echo "[4.1] File-level localization (relevant)"
python agentless/fl/localize_java_local.py \
  --file_level \
  --output_folder results/poc-bench-lite/file_level \
  --num_threads 1 \
  --skip_existing \
  --target_id "${TARGET_ID}"

echo "[4.1] File-level localization (irrelevant)"
python agentless/fl/localize_java_local.py \
  --file_level \
  --irrelevant \
  --output_folder results/poc-bench-lite/file_level_irrelevant \
  --num_threads 1 \
  --skip_existing \
  --target_id "${TARGET_ID}"

echo "[4.1] Retrieval based on irrelevant files"
python agentless/fl/retrieve_java_local.py \
  --index_type simple \
  --filter_type given_files \
  --filter_file results/poc-bench-lite/file_level_irrelevant/loc_outputs.jsonl \
  --output_folder results/poc-bench-lite/retrievel_embedding \
  --persist_dir embedding/poc-bench_simple \
  --num_threads 1 \
  --target_id "${TARGET_ID}"

echo "[4.1] Combine retrieval + model localization"
python agentless/fl/combine.py \
  --retrieval_loc_file results/poc-bench-lite/retrievel_embedding/retrieve_locs.jsonl \
  --model_loc_file results/poc-bench-lite/file_level/loc_outputs.jsonl \
  --top_n 3 \
  --output_folder results/poc-bench-lite/file_level_combined


echo "[4.2] Related element localization"
python agentless/fl/localize_java_local.py \
  --related_level \
  --output_folder results/poc-bench-lite/related_elements \
  --top_n 3 \
  --compress_assign \
  --compress \
  --start_file results/poc-bench-lite/file_level_combined/combined_locs.jsonl \
  --num_threads 1 \
  --skip_existing \
  --target_id "${TARGET_ID}"


echo "[4.3] Fine-grain line-level localization (sampling)"
python agentless/fl/localize_java_local.py \
  --fine_grain_line_level \
  --output_folder results/poc-bench-lite/edit_location_samples \
  --top_n 3 \
  --compress \
  --temperature 0.8 \
  --num_samples 4 \
  --start_file results/poc-bench-lite/related_elements/loc_outputs.jsonl \
  --num_threads 1 \
  --skip_existing \
  --target_id "${TARGET_ID}"

echo "[4.3] Merge edit locations"
python agentless/fl/localize_java_local.py \
  --merge \
  --output_folder results/poc-bench-lite/edit_location_individual \
  --top_n 3 \
  --num_samples 4 \
  --start_file results/poc-bench-lite/edit_location_samples/loc_outputs.jsonl

echo "=========================================="
echo "Localization pipeline finished successfully"
echo "=========================================="
