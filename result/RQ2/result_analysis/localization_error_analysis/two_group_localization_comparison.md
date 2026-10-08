# Comparison of normalized-patch localization statistics across the two groups

The decision criterion is the same: a generated patch is judged correctly localized as soon as it and the same-named baseline patch modify at least one identical repository-relative file path.

| Data group | patch_total | localization_correct | localization_error | error_rate | error_patches_after_dedup |
|---|---:|---:|---:|---:|---:|
| With vulnerability chain | 503 | 453 | 50 | 9.94% | 15 |
| CVE description | 460 | 386 | 74 | 16.09% | 29 |

## Per-method comparison

| method | with_vuln_chain: total | with_vuln_chain: errors | cve_description: total | cve_description: errors |
|---|---:|---:|---:|---:|
| agentless | 54 | 8 | 57 | 11 |
| appatch | 63 | 3 | 49 | 9 |
| openhands | 62 | 1 | 62 | 4 |
| patchagent | 60 | 2 | 40 | 6 |
| premm | 48 | 11 | 49 | 11 |
| reinfix | 63 | 11 | 63 | 11 |
| repairagent | 53 | 1 | 40 | 10 |
| san2patch | 43 | 10 | 41 | 10 |
| sweagent | 57 | 3 | 59 | 2 |
| **Total** | **503** | **50** | **460** | **74** |

Compared with the vulnerability-chain group, the CVE-description group has 24 more localization-error instances and an error rate 6.15 percentage points higher.