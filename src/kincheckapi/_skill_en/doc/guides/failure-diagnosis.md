# Failure Diagnosis Rules

1. Distinguish input, assembly, Scenario, backend, and check stages; do not summarize every failure as “the model cannot move”.
2. Catch structured `KinCheckError` subclasses and read `code`, `message`, `object_ids`, `report`, and `suggested_actions`.
3. Prefer `try_solve_motion()` on solve failure to retain `last_valid_result`, failure time, residuals, and the last frame.
4. Use `partial` results to locate the first failing joint or closure, but always mark them incomplete.
5. Print public errors or results, or use `diagnostics.explain_issue()` and `format_report_for_agent()` for explanation; call `write_report()` only when persistence is requested.
6. If the cause is geometry, assembly, or export definition, modify the SimpleCADAPI model and export again; never silently rewrite model semantics in the verifier.
7. Keep the original acceptance conditions unchanged. Change verifier thresholds, scope, or exclusions only when the user changes the mechanism requirements.
