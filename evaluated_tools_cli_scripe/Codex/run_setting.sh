#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)

if (($# == 0)); then
    printf 'usage: %s {baseline|downstream_poc|vpp|upstream_repository|gt_upstream_patch} [runner options...]\n' "$0" >&2
    exit 2
fi

setting=$1
shift

case "$setting" in
    baseline)
        experiment=issue_only_CVE_discribtions
        prompt_dir=baseline_vuln_desc
        ;;
    downstream_poc)
        experiment=issue_with_poc
        prompt_dir=downstream_poc
        ;;
    vpp)
        experiment=issue_with_chains
        prompt_dir=vpp_injection
        ;;
    upstream_repository)
        experiment=issue_with_upstream_repo
        prompt_dir=upstream_accessible
        ;;
    gt_upstream_patch)
        experiment=issue_with_upstream_patches
        prompt_dir=gt_upstream_patch
        ;;
    *)
        printf 'error: unknown setting: %s\n' "$setting" >&2
        exit 2
        ;;
esac

export CODEX_REPOS_DIR=${CODEX_REPOS_DIR:-"$PROJECT_ROOT/dataset/downstream_repo"}
export CODEX_PROMPTS_DIR="$PROJECT_ROOT/issue/$prompt_dir"
export CODEX_RESULTS_ROOT=${CODEX_RESULTS_ROOT:-"$SCRIPT_DIR/raw_results"}

exec "$SCRIPT_DIR/run_codex_repairs.sh" \
    --experiment "$experiment" \
    --model gpt-5.6-luna \
    --reasoning-effort low \
    "$@"
