# Upstream vs downstream vulnerability repair comparison

## Result

- Common vulnerabilities: 40; corresponding downstream project tasks: 63; tools: 9.
- Overall upstream repair rate: 30.3% (bootstrap 95% CI 20.8%–40.0%).
- Overall downstream repair rate: 38.0% (bootstrap 95% CI 30.4%–45.2%).
- Difference (upstream − downstream): -7.7 percentage points (paired bootstrap 95% CI -19.5 to +4.4 percentage points).
- Of the 9 tools, 2 have a higher upstream repair rate and 7 have a higher downstream repair rate.

The current results do not support the inference that "upstream is easier to repair". The point estimate actually shows downstream 7.7 percentage points higher; but the difference confidence interval spans 0, so downstream cannot be asserted to be necessarily easier to repair either.

## Statistical criteria

1. Only vulnerabilities appearing in both tables are compared. The 3 upstream-only vulnerabilities (CVE-2020-13973, CVE-2020-5408, CVE-2022-23596) do not enter the main comparison; downstream-only vulnerabilities: none.
2. When aligning, downstream `Zip-263` and upstream `Zip4j-263` are treated as the same vulnerability, and downstream `san2patch` and upstream `San2Agent` as the same tool, displayed as `San2Patch`.
3. "Repaired" refers only to upstream `Fixed` or downstream `success`. `Compilation Failed/compile_error`, `Not Fixed/repair_failed` and `No Patch/empty` all count in the denominator.
4. The same vulnerability may correspond to multiple downstream projects. The main chart first computes the downstream-project repair ratio for each "vulnerability × tool" pair, then averages with equal weight over the 40 vulnerabilities; this prevents vulnerabilities with more downstream projects from receiving a higher weight.
5. The confidence interval comes from 10,000 bootstrap resamples with the vulnerability as the unit and a fixed random seed of 20260818. It describes sampling uncertainty and is not causal proof of a difficulty difference between upstream and downstream.
6. `repair_rate_summary.csv` also provides the micro repair rate weighted directly by downstream task, for sensitivity checks.

## Files

- `repair_rate_comparison.svg/.png`: per-tool repair-rate bar chart with 95% CI.
- `dumbbell_plot.svg/.png`: per-tool upstream-vs-downstream difference dumbbell chart.
- `repair_rate_summary.csv`: summary repair rates, confidence intervals and both downstream weighting schemes.
- `matched_cve_details.csv`: per-tool paired detail for the common vulnerabilities.
- `generate_comparison.py`: regenerates all results from the two source CSVs.
- `render_png.py`: PNG fallback renderer used when the default Python has no plotting library.