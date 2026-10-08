# Cases where three groups are repair_failed and the combined group repairs successfully

## Conclusion

Under the strict criterion a total of **9 `<tool, patch>` pairs** were found.

Strict decision conditions:

- `with_vuln_chain_validation_matrix.csv == repair_failed`
- `cve_description_validation_matrix.csv == repair_failed`
- `with_selfgen_upstream_patch_matrix.csv == repair_failed`
- `with_selfgen_upstream_patch_and_vuln_chain_matrix.csv == success`

All four matrices have the same 567 `target_id × tool` keys (63 targets, 9 tools), so there are no missed pairings caused by missing rows or missing tools.

## All strict-criterion cases

1. `patchagent` × `CODEC-263_DBlog-master.patch`
2. `repairagent` × `CODEC-263_DBlog-master.patch`
3. `repairagent` × `CVE-2017-7957_cqrs-lottery-master.patch`
4. `premm` × `CVE-2021-23899_json-sanitizer.patch`
5. `sweagent` × `CVE-2021-39144_source.patch`
6. `openhands` × `CVE-2021-43859_rpki-commons.patch`
7. `repairagent` × `CVE-2022-25845_geek_framework.patch`
8. `repairagent` × `CVE-2022-29631_ucloud-java-sdk.patch`
9. `repairagent` × `CVE-2022-45688_virtress.patch`

Counted by tool: openhands 1 pair, patchagent 1 pair, premm 1 pair, repairagent 5 pairs, sweagent 1 pair.

The four-group states, successful-patch paths, SHA-256 and file sizes are in `all_cases_strict.csv`; the corresponding successful patches have been copied to `successful_patches/`.

## Relaxed-criterion appendix

If `compile_error` and `empty` are also counted as "not repaired successfully", there are 35 pairs in total. The complete list is in `appendix_first_three_groups_all_fail.csv`, where the 9 pairs above are marked with "also belongs to the strict criterion".

## Data sources and reproduction

- `Vulnerability chain`: `with_vuln_chain_validation_matrix.csv`
- `CVE description`: `cve_description_validation_matrix.csv`
- `Self-generated upstream patch`: `with_selfgen_upstream_patch_matrix.csv`
- `Self-generated upstream patch + vulnerability chain`: `with_selfgen_upstream_patch_and_vuln_chain_matrix.csv`

The combined experiment uses the latest complete batch: `带自生成上游补丁加漏洞链验证结果/nine_patch_validation_20260830_202357/pipeline_summary.json`.

Running `python3 generate_results.py` in this directory recomputes the list and refreshes the patch copies. The script verifies that the tool columns and all keys of the four matrices are exactly identical.