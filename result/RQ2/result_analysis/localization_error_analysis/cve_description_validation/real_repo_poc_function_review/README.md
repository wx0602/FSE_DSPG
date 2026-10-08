# CVE-description group: real-repository PoC function-localization review

A total of **74** instances whose file paths do not overlap were reviewed:

- **40** genuinely localized to an unrelated function;
- **34** are still on the PoC's direct call, downstream call, or inheritance chain, so they cannot be counted as function-localization errors.

The verdict relies only on the original-repository PoC source, the call/inheritance relationships and the patch hunks; the PoC vulnerability-string counts are kept only in the per-case reports as run observations and do not feed into the function-localization conclusion.

- `summary.csv`: all 74 items with the basis for each one.
- `localized_to_unrelated_function.csv`: only the genuinely unrelated instances.
- `method__target.md`: one standalone report per patch instance.