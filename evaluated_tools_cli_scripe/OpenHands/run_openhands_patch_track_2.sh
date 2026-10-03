#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --target_id=<CVE>_<repo>"
  echo "Example: $0 --target_id=CVE-2017-7957_cqrs-lottery-master"
}

# ---- parse args ----
target_id=""
for arg in "$@"; do
  case "$arg" in
    --target_id=*)
      target_id="${arg#*=}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$target_id" ]]; then
  echo "Error: --target_id is required."
  usage
  exit 1
fi

# ---- split by the FIRST underscore ----
if [[ "$target_id" != *_* ]]; then
  echo "Error: target_id must contain an underscore '_' to split CVE and repo."
  echo "Got: $target_id"
  exit 1
fi

cve="${target_id%%_*}"        # before first _
repo_name="${target_id#*_}"   # after first _

# ---- base paths ----
repo="${BASE_RES}/resource/${cve}/${repo_name}"
repo_copy="${BASE_RES}/resource_openhands_result/${target_id}"
patch="${BASE_RES}/resource_openhands_result/openhands_patches_track_2/${target_id}_openhands.diff"
BASE_RES="./VESTa_resource"
issue="${BASE_RES}/issue/63_issues_2_track/${target_id}.md"


# ---- run python to generate patch ----
echo "[INFO] target_id:   $target_id"
echo "[INFO] cve:         $cve"
echo "[INFO] repo_name:   $repo_name"
echo "[INFO] repo:        $repo"
echo "[INFO] repo_copy:   $repo_copy"
echo "[INFO] patch:       $patch"
echo "[INFO] issue:       $issue"

python openhands_repo2patch.py \
  --repo="$repo" \
  --repo_copy="$repo_copy" \
  --patch="$patch" \
  --issue="$issue"

# ---- check patch and docker cp ----
if [[ -f "$patch" ]]; then
  echo "[INFO] Patch generated: $patch"
  container_id="9a401de53fa9"
  container_path="/VESTA/resource/openhands/openhands_patch_track_2/"

  echo "[INFO] Copying patch into container ${container_id}:${container_path}"
  docker cp "$patch" "${container_id}:${container_path}"
  echo "[OK] Done."
else
  echo "[ERROR] Patch file not found after generation: $patch"
  exit 2
fi
