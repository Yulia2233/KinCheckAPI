# Evidence and Pass Rules

An Agent may say “pass” only when all of the following hold:

- inputs and check parameters are finite and within range;
- assembly and Scenario prechecks pass;
- `MotionResult.status` is not `partial` and contains actual samples;
- the relevant check has non-zero samples, component pairs, or measurements;
- no unhandled error-severity issue remains;
- evidence satisfies the user's thresholds;
- check scope and exclusions match the user's intent.

The verification program should call `raise_if_failed()` (or equivalent `diagnostics.assert_check_passed()`) so the CLI exits non-zero on failure. Keep `passed`, `status`, counts, thresholds, extrema, and issue codes in console output; persist a report only when explicitly requested.

Write acceptance conditions into the verifier before implementing the SimpleCADAPI model. Unless the user changes the claim, do not relax thresholds, remove checks, reduce sampling, or add unjustified exclusions to make a model pass.
