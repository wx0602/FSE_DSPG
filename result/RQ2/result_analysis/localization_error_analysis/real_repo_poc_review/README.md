# Real-repository PoC localization review

This directory reviews, case by case, 50 patch instances whose modified files do not intersect the baseline's.

- Original-repository PoC function path confirmed unrelated: 15
- Original-repository PoC function path related: 35

- PoC supports a suspected function-localization error: 18
- PoC verification effective (not a localization error): 16
- Not verified (compile/run error, or not comparable): 16

The original-repository function-path conclusion is based on the classes/methods the PoC actually calls, the inheritance relationships and the patch hunks; PoC run counts serve only as supporting evidence.
