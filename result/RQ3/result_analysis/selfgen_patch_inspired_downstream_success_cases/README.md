# Cases where the self-generated upstream patch failed but inspired a successful downstream repair

This directory collects 3 cases that were manually reviewed at the code level. Selection criteria:

1. The same tool's result on the upstream repository is not Fixed.
2. The same tool is success in the downstream "with self-generated upstream patch" experiment.
3. The strict "all PoCs pass (AND)" criterion is used.
4. After manual comparison, the upstream attempt and the downstream successful patch share the same security intent, but differ in where or how the fix is applied.

Each subdirectory contains the upstream failed patch, the downstream successful patch and the case analysis.

Note: these cases support the mechanistic explanation that "a failed upstream attempt can still provide useful repair intent", but the validation
results themselves do not directly prove the model's internal "understanding" process.