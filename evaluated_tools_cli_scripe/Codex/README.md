# Codex experiment adapter

This directory contains the Codex CLI batch runner used for the DSPG-Bench
experiments and the exporter used to place production-source patches into the
repository's `result/` layout.

## Included completed settings

| Runner experiment | DSPG-Bench issue input | Exported result |
|---|---|---|
| `issue_only_CVE_discribtions` | `issue/baseline_vuln_desc` | `result/RQ1/baseline/codex` |
| `issue_with_poc` | `issue/downstream_poc` | `result/RQ1/with_downstream_poc/codex` |
| `issue_with_chains` | `issue/vpp_injection` | `result/RQ2/with_vpp/codex` |
| `issue_with_upstream_repo` | `issue/upstream_accessible` | `result/RQ3/with_upstream_repository/codex` |
| `issue_with_upstream_patches` | `issue/gt_upstream_patch` | `result/RQ3/with_gt_upstream_patch/codex` |

The unfinished Codex runs for RQ3 Bootstrapped Repair and RQ4 Combined Strategy
are intentionally not included.

## Configuration used

- Codex CLI: `0.153.4`
- Reasoning effort: `low`
- Model: `gpt-5.6-luna` for 313 of the 315 exported downstream patches
- Baseline exceptions: `CODEC-263_DBlog-master` and `CVE-2022-42889_java`
  were generated with `gpt-5.5`
- Network, web search, plugins, apps, skills, hooks, and multi-agent execution
  were disabled
- Codex edited only temporary worktrees; benchmark repositories were read-only
- `pom.xml` and test-path changes were removed from exported patches

## Running a setting

`run_setting.sh` maps DSPG-Bench setting names to the original runner names and
issue directories. Raw logs and nested patches are written below
`evaluated_tools_cli_scripe/Codex/raw_results/` unless `CODEX_RESULTS_ROOT` is
set explicitly.

```bash
./run_setting.sh baseline
./run_setting.sh downstream_poc
./run_setting.sh vpp
./run_setting.sh upstream_repository
./run_setting.sh gt_upstream_patch
```

Additional runner options such as `--task`, `--model`,
`--reasoning-effort`, `--timeout`, and `--fast` may follow the setting name.

The packaged downstream repositories contain PoCs. For a baseline reproduction,
point `CODEX_REPOS_DIR` at a prepared copy with downstream tests/PoCs withheld,
matching the experimental protocol.

## Export format

Each completed result directory contains one `<task>.patch` per benchmark
instance plus `normalize_report.json`. The report records the model, reasoning
effort, status, SHA-256 digest, and modified production Java paths for every
patch. Empty patches, failed tasks, dependency-file changes, and test changes
are rejected by the exporter.

