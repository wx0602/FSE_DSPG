#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)

REPOS_DIR=${CODEX_REPOS_DIR:-"$PROJECT_ROOT/downstream_dataset/resource_no_test2"}
REPO_SUBDIR=${CODEX_REPO_SUBDIR:-}
RESULTS_ROOT=${CODEX_RESULTS_ROOT:-"$SCRIPT_DIR/results"}
MODEL=${CODEX_MODEL:-gpt-5.6-luna}
REASONING_EFFORT=${CODEX_REASONING_EFFORT:-low}
SANDBOX_MODE=${CODEX_SANDBOX_MODE:-workspace-write}
TIMEOUT_SECONDS=${CODEX_TIMEOUT_SECONDS:-3600}
FAST_MODE=${CODEX_FAST_MODE:-0}
CODEX_STATE_HOME=${CODEX_HOME:-"${HOME:-}/.codex"}

# Host skill discovery can be disabled as a feature, while bundled system
# skills need explicit per-skill overrides.
DISABLED_SYSTEM_SKILLS="skills.config=[{path=\"$CODEX_STATE_HOME/skills/.system/imagegen/SKILL.md\",enabled=false},{path=\"$CODEX_STATE_HOME/skills/.system/openai-docs/SKILL.md\",enabled=false},{path=\"$CODEX_STATE_HOME/skills/.system/plugin-creator/SKILL.md\",enabled=false},{path=\"$CODEX_STATE_HOME/skills/.system/skill-creator/SKILL.md\",enabled=false},{path=\"$CODEX_STATE_HOME/skills/.system/skill-installer/SKILL.md\",enabled=false}]"

FORCE=0
DRY_RUN=0
LIST_ONLY=0
EXPERIMENT=issue_only_CVE_discribtions
VARIANT=
RESULT_DIR_OVERRIDE=
declare -a REQUESTED_TASKS=()

usage() {
    cat <<'EOF'
Usage: ./run_codex_repairs.sh [options]

Run every prompt/repository pair by default.

Options:
  --experiment NAME         Select a supported issue group
  --variant NAME            Select a nested prompt source (required for
                            issue_with_all and issue_with_upresult)
  --result-dir DIR          Write outputs directly to DIR instead of the
                            default results/<experiment>/<variant> directory
  --task NAME               Run one task (repeatable; .md is optional)
  --model MODEL             Codex model (default: gpt-5.6-luna)
  --reasoning-effort LEVEL  Reasoning effort (default: low)
  --timeout SECONDS         Per-task timeout; 0 disables it (default: 3600)
  --fast                    Use Codex Fast mode for every model request
  --force                   Rerun tasks that already have a status file
  --dry-run                 Validate and print selected tasks without Codex calls
  --list                    List all valid task names and exit
  -h, --help                Show this help

Environment overrides:
  CODEX_REPOS_DIR, CODEX_REPO_SUBDIR, CODEX_PROMPTS_DIR,
  CODEX_RESULTS_ROOT, CODEX_MODEL, CODEX_REASONING_EFFORT,
  CODEX_SANDBOX_MODE, CODEX_TIMEOUT_SECONDS, CODEX_FAST_MODE
EOF
}

die() {
    printf 'error: %s\n' "$*" >&2
    exit 2
}

while (($# > 0)); do
    case "$1" in
        --experiment)
            (($# >= 2)) || die "--experiment requires a value"
            EXPERIMENT=$2
            shift 2
            ;;
        --variant)
            (($# >= 2)) || die "--variant requires a value"
            VARIANT=$2
            shift 2
            ;;
        --result-dir)
            (($# >= 2)) || die "--result-dir requires a value"
            RESULT_DIR_OVERRIDE=$2
            shift 2
            ;;
        --task)
            (($# >= 2)) || die "--task requires a value"
            REQUESTED_TASKS+=("${2%.md}")
            shift 2
            ;;
        --model)
            (($# >= 2)) || die "--model requires a value"
            MODEL=$2
            shift 2
            ;;
        --reasoning-effort)
            (($# >= 2)) || die "--reasoning-effort requires a value"
            REASONING_EFFORT=$2
            shift 2
            ;;
        --timeout)
            (($# >= 2)) || die "--timeout requires a value"
            TIMEOUT_SECONDS=$2
            shift 2
            ;;
        --fast)
            FAST_MODE=1
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --list)
            LIST_ONLY=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

case "$EXPERIMENT" in
    issue_only_CVE_discribtions|issue_with_all|issue_with_chains|issue_with_poc|\
    issue_with_upresult|issue_with_upstream_patches|issue_with_upstream_repo|upstream_issue)
        ;;
    *)
        die "unknown experiment: $EXPERIMENT"
        ;;
esac

PROMPTS_ROOT="$PROJECT_ROOT/issue/$EXPERIMENT"
RESULT_DIR="$RESULTS_ROOT/$EXPERIMENT"
if [[ -n "$VARIANT" ]]; then
    [[ "$VARIANT" =~ ^[A-Za-z0-9._-]+$ ]] || die "invalid variant name: $VARIANT"
    PROMPTS_ROOT="$PROMPTS_ROOT/$VARIANT"
    RESULT_DIR="$RESULT_DIR/$VARIANT"
elif [[ "$EXPERIMENT" == issue_with_all || "$EXPERIMENT" == issue_with_upresult ]]; then
    die "$EXPERIMENT requires --variant; available variants: agentless appatch openhands patchagent premm reinfix repairagent san2patch sweagent"
fi

if [[ -n "$RESULT_DIR_OVERRIDE" ]]; then
    if [[ "$RESULT_DIR_OVERRIDE" == /* ]]; then
        RESULT_DIR=$RESULT_DIR_OVERRIDE
    else
        RESULT_DIR="$SCRIPT_DIR/$RESULT_DIR_OVERRIDE"
    fi
fi

PROMPTS_DIR=${CODEX_PROMPTS_DIR:-"$PROMPTS_ROOT"}
PATCH_DIR="$RESULT_DIR/patches"
LOG_DIR="$RESULT_DIR/logs"
MESSAGE_DIR="$RESULT_DIR/final_messages"
INPUT_DIR="$RESULT_DIR/prompt_inputs"
STATUS_DIR="$RESULT_DIR/status"
SUMMARY_FILE="$RESULT_DIR/run_status.tsv"

if [[ -n "$REPO_SUBDIR" ]]; then
    [[ "$REPO_SUBDIR" =~ ^[A-Za-z0-9._/-]+$ ]] \
        || die "invalid repository subdirectory: $REPO_SUBDIR"
    [[ "$REPO_SUBDIR" != /* && "/$REPO_SUBDIR/" != *"/../"* ]] \
        || die "repository subdirectory must be a safe relative path: $REPO_SUBDIR"
fi

repository_for_task() {
    local task=$1
    local repository="$REPOS_DIR/$task"

    if [[ -n "$REPO_SUBDIR" ]]; then
        repository="$repository/$REPO_SUBDIR"
    fi
    printf '%s\n' "$repository"
}

[[ -d "$REPOS_DIR" ]] || die "repository directory does not exist: $REPOS_DIR"
[[ -d "$PROMPTS_DIR" ]] || die "prompt directory does not exist: $PROMPTS_DIR"
[[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] || die "timeout must be a non-negative integer"
[[ "$FAST_MODE" =~ ^[01]$ ]] || die "CODEX_FAST_MODE must be 0 or 1"
command -v codex >/dev/null 2>&1 || die "codex is not available on PATH"
command -v git >/dev/null 2>&1 || die "git is not available on PATH"
if ((TIMEOUT_SECONDS > 0)); then
    command -v timeout >/dev/null 2>&1 || die "timeout is not available on PATH"
fi

mapfile -t ALL_TASKS < <(
    find "$PROMPTS_DIR" -maxdepth 1 -type f -name '*.md' -printf '%f\n' \
        | sed 's/\.md$//' \
        | sort
)
((${#ALL_TASKS[@]} > 0)) || die "no Markdown prompts found in $PROMPTS_DIR"

declare -A VALID_TASKS=()
for task in "${ALL_TASKS[@]}"; do
    source_repo=$(repository_for_task "$task")
    [[ -d "$source_repo" ]] \
        || die "prompt has no usable same-named repository: $task ($source_repo)"
    VALID_TASKS["$task"]=1
done

while IFS= read -r repo_name; do
    [[ "$repo_name" == "files" ]] && continue
    [[ -n "${VALID_TASKS[$repo_name]+x}" ]] \
        || die "repository has no same-named prompt: $repo_name"
done < <(find "$REPOS_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)

if ((LIST_ONLY)); then
    printf '%s\n' "${ALL_TASKS[@]}"
    exit 0
fi

declare -a TASKS=()
if ((${#REQUESTED_TASKS[@]} > 0)); then
    for task in "${REQUESTED_TASKS[@]}"; do
        [[ -n "${VALID_TASKS[$task]+x}" ]] || die "unknown task: $task"
        TASKS+=("$task")
    done
else
    TASKS=("${ALL_TASKS[@]}")
fi

if ((DRY_RUN)); then
    printf 'experiment=%s variant=%s model=%s reasoning_effort=%s fast_mode=%s sandbox=%s timeout=%s\n' \
        "$EXPERIMENT" "${VARIANT:--}" "$MODEL" "$REASONING_EFFORT" \
        "$FAST_MODE" "$SANDBOX_MODE" "$TIMEOUT_SECONDS"
    printf 'prompts=%s\nrepositories_read_only=%s\nresults=%s\nworkspace=temporary\n' \
        "$PROMPTS_DIR" "$REPOS_DIR" "$RESULT_DIR"
    for task in "${TASKS[@]}"; do
        printf '%s\t%s\t%s\n' \
            "$task" "$PROMPTS_DIR/$task.md" "$(repository_for_task "$task")"
    done
    exit 0
fi

mkdir -p -- "$PATCH_DIR" "$LOG_DIR" "$MESSAGE_DIR" "$INPUT_DIR" "$STATUS_DIR"
if [[ ! -e "$SUMMARY_FILE" ]]; then
    printf 'task\tstatus\tcodex_exit\tpatch_bytes\tstarted_at\tfinished_at\tmodel\treasoning_effort\n' \
        > "$SUMMARY_FILE"
fi

TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/codex-repairs.XXXXXX")
cleanup() {
    case "$TMP_ROOT" in
        "${TMPDIR:-/tmp}"/codex-repairs.*) rm -rf -- "$TMP_ROOT" ;;
    esac
}
trap cleanup EXIT
trap 'exit 130' INT TERM

EXCLUDES_FILE="$TMP_ROOT/baseline-excludes"
cat > "$EXCLUDES_FILE" <<'EOF'
.git/
target/
build/
dist/
out/
bin/
.gradle/
node_modules/
.idea/
.vscode/
*.class
*.jar
*.war
*.ear
*.log
*.zip
*.tar
*.tar.gz
*.tgz
*.7z
EOF

write_prompt_input() {
    local task=$1
    local destination=$2

    cat > "$destination" <<EOF
Act as the implementation agent for the vulnerability repair experiment below. Work directly in the current repository and complete the repair end to end.

Requirements for this run:
- Inspect the repository and identify the vulnerable behavior or dependency usage described by the task.
- Implement the best source-level mitigation that satisfies every constraint in the task, especially the prohibition on upgrading the vulnerable library.
- Add or update focused tests when practical, and run the most relevant available tests.
- Make actual code changes even if a complete fix cannot be verified. Do not stop after analysis or only describe a patch.
- Keep the change narrowly scoped. Do not edit generated files, dependency caches, build output directories, or unrelated code.
- Do not use web search, network access, skills, plugins, apps, MCP servers, or sub-agents. Base the repair only on the supplied task and local repository contents.
- Leave all repair changes in the working tree. Do not commit, reset, or discard them.
- In the final response, briefly state what changed and which tests were run.

The experiment task follows verbatim.

EOF
    cat "$PROMPTS_DIR/$task.md" >> "$destination"
}

create_baseline() {
    local repo=$1
    local git_dir=$2
    local tree commit

    git init --bare -q "$git_dir" || return 1
    git --git-dir="$git_dir" config core.excludesFile "$EXCLUDES_FILE" || return 1
    git --git-dir="$git_dir" config core.autocrlf false || return 1
    git -C "$repo" --git-dir="$git_dir" --work-tree="$repo" add -A -- . || return 1
    tree=$(git --git-dir="$git_dir" write-tree) || return 1
    commit=$(
        printf 'Codex experiment baseline\n' \
            | GIT_AUTHOR_NAME=codex-experiment \
                GIT_AUTHOR_EMAIL=codex-experiment@localhost \
                GIT_COMMITTER_NAME=codex-experiment \
                GIT_COMMITTER_EMAIL=codex-experiment@localhost \
                git --git-dir="$git_dir" commit-tree "$tree"
    ) || return 1
    printf '%s\n' "$commit"
}

materialize_worktree() {
    local git_dir=$1
    local worktree=$2

    mkdir -p -- "$worktree" || return 1
    git --git-dir="$git_dir" --work-tree="$worktree" \
        checkout-index --all --force || return 1
}

export_patch() {
    local repo=$1
    local git_dir=$2
    local baseline_commit=$3
    local patch_file=$4

    git -C "$repo" --git-dir="$git_dir" --work-tree="$repo" add -A -- . || return 1
    git -C "$repo" --git-dir="$git_dir" --work-tree="$repo" \
        diff --cached --binary --full-index --no-ext-diff --no-renames \
        "$baseline_commit" -- > "$patch_file" || return 1

    filter_patch_paths "$patch_file"
}

filter_patch_paths() {
    local patch_file=$1
    local filtered_file="${patch_file}.filtered.$$"

    awk '
        function excluded(path, lower) {
            lower = tolower(path)
            return lower ~ /(^|\/)pom\.xml$/ \
                || lower ~ /(^|\/)src\/test\// \
                || lower ~ /(^|\/)(test|tests)\// \
                || path ~ /(^|\/)[^\/]*(Test|Tests|TestCase)\.(java|kt|groovy|scala)$/ \
                || lower ~ /(^|\/)[^\/]*_test\.go$/ \
                || lower ~ /(^|\/)test_[^\/]*\.py$/ \
                || lower ~ /\.(test|spec)\.(js|ts|jsx|tsx)$/
        }

        /^diff --git / {
            path = $4
            sub(/^b\//, "", path)
            keep = !excluded(path)
        }

        keep { print }
    ' "$patch_file" > "$filtered_file" || return 1

    mv -- "$filtered_file" "$patch_file"
}

overall_rc=0
printf '[config] experiment=%s variant=%s model=%s reasoning_effort=%s fast_mode=%s\n' \
    "$EXPERIMENT" "${VARIANT:--}" "$MODEL" "$REASONING_EFFORT" "$FAST_MODE"
for task in "${TASKS[@]}"; do
    source_repo=$(repository_for_task "$task")
    prompt_input="$INPUT_DIR/$task.txt"
    event_log="$LOG_DIR/$task.jsonl"
    final_message="$MESSAGE_DIR/$task.txt"
    task_patch_dir="$PATCH_DIR/$task"
    patch_file="$task_patch_dir/patch.diff"
    status_file="$STATUS_DIR/$task.tsv"

    if [[ -e "$status_file" && "$FORCE" -eq 0 ]]; then
        printf '[skip] %s (status already exists; use --force to rerun)\n' "$task"
        continue
    fi

    started_at=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    printf '[run ] %s\n' "$task"
    mkdir -p -- "$task_patch_dir"
    : > "$patch_file"
    write_prompt_input "$task" "$prompt_input"
    : > "$event_log"
    : > "$final_message"

    task_tmp="$TMP_ROOT/$task"
    baseline_git="$task_tmp/baseline.git"
    repo="$task_tmp/worktree"
    mkdir -p -- "$task_tmp"
    if ! baseline_commit=$(create_baseline "$source_repo" "$baseline_git"); then
        printf '[fail] %s: could not create pre-run baseline\n' "$task" >&2
        finished_at=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
        status=baseline_failed
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$task" "$status" -1 0 "$started_at" "$finished_at" "$MODEL" "$REASONING_EFFORT" \
            | tee "$status_file" >> "$SUMMARY_FILE"
        overall_rc=1
        continue
    fi
    if ! materialize_worktree "$baseline_git" "$repo"; then
        printf '[fail] %s: could not create temporary worktree\n' "$task" >&2
        finished_at=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
        status=worktree_failed
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$task" "$status" -1 0 "$started_at" "$finished_at" "$MODEL" "$REASONING_EFFORT" \
            | tee "$status_file" >> "$SUMMARY_FILE"
        overall_rc=1
        continue
    fi

    codex_command=(
        codex exec
        --model "$MODEL"
        --config "model_reasoning_effort=\"$REASONING_EFFORT\""
        --config 'web_search="disabled"'
        --config 'sandbox_workspace_write.network_access=false'
        --config "$DISABLED_SYSTEM_SKILLS"
        --sandbox "$SANDBOX_MODE"
        --ignore-user-config
        --strict-config
        --enable skip_host_skill_discovery
        --disable skill_search
        --disable plugins
        --disable apps
        --disable multi_agent
        --disable hooks
        --skip-git-repo-check
        --json
        --output-last-message "$final_message"
        --cd "$repo"
    )
    if ((FAST_MODE)); then
        codex_command+=(
            --config 'service_tier="fast"'
            --enable fast_mode
        )
    fi
    codex_command+=(-)

    if ((TIMEOUT_SECONDS > 0)); then
        timeout --signal=INT --kill-after=30 "$TIMEOUT_SECONDS" \
            "${codex_command[@]}" < "$prompt_input" > "$event_log" 2>&1
        codex_rc=$?
    else
        "${codex_command[@]}" < "$prompt_input" > "$event_log" 2>&1
        codex_rc=$?
    fi

    if ! export_patch "$repo" "$baseline_git" "$baseline_commit" "$patch_file"; then
        printf '[fail] %s: patch export failed\n' "$task" >&2
        status=patch_export_failed
        patch_bytes=0
        overall_rc=1
    else
        patch_bytes=$(wc -c < "$patch_file")
        if ((patch_bytes == 0)); then
            status=no_patch
            overall_rc=1
        elif ((codex_rc == 0)); then
            status=patched
        else
            status=patched_codex_failed
            overall_rc=1
        fi
    fi

    finished_at=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$task" "$status" "$codex_rc" "$patch_bytes" "$started_at" "$finished_at" \
        "$MODEL" "$REASONING_EFFORT" \
        | tee "$status_file" >> "$SUMMARY_FILE"
    printf '[done] %s status=%s codex_exit=%s patch_bytes=%s\n' \
        "$task" "$status" "$codex_rc" "$patch_bytes"
done

exit "$overall_rc"
