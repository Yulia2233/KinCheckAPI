# Structured Diagnostics

Collect, explain, and persist stable error codes, evidence, and failure context.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`AgentGuidance`](AgentGuidance.md) | Type | Stable repair guidance associated with one public error code. |
| [`AgentReadableResult`](AgentReadableResult.md) | Type | Shared outward-facing behavior for public diagnostic result objects. |
| [`BackendFailure`](BackendFailure.md) | Type | Sanitized evidence copied from a private calculation backend. |
| [`DiagnosticReport`](DiagnosticReport.md) | Type | Complete diagnostic context attached to a public KinCheckAPI error. |
| [`Evidence`](Evidence.md) | Type | One machine-readable fact supporting a diagnostic conclusion. |
| [`Fix`](Fix.md) | Type | A deliberately small mechanical patch description. |
| [`IssueExplanation`](IssueExplanation.md) | Type | Agent-facing explanation without depending on free-form exception text. |
| [`Severity`](Severity.md) | Type alias | Define the public type contract used by `Severity`. |
| [`SimIssue`](SimIssue.md) | Type | A stable, actionable issue produced by validation or verification. |
| [`ValidationResult`](ValidationResult.md) | Type | Aggregated validation outcome; validation itself never fails fast. |
| [`apply_assembly_fix`](apply_assembly_fix.md) | Function | Reserved automatic-fix entry point; v0.5.0 is unimplemented and raises `BackendCapabilityError`. |
| [`apply_scenario_fix`](apply_scenario_fix.md) | Function | Reserved automatic-fix entry point; v0.5.0 is unimplemented and raises `BackendCapabilityError`. |
| [`assert_check_passed`](assert_check_passed.md) | Function | Require a structured check to pass; otherwise raise `VerificationError` while preserving the original check. |
| [`collect_issues`](collect_issues.md) | Function | Collect and content-deduplicate `SimIssue` objects from multiple structured results. |
| [`create_backend_failure_report`](create_backend_failure_report.md) | Function | Sanitize an unknown backend exception and optional partial result into a stable `DiagnosticReport`. |
| [`create_report`](create_report.md) | Function | Combine issues from assembly, Scenario, motion, geometric safety, and checks into one `DiagnosticReport`. |
| [`explain_issue`](explain_issue.md) | Function | Expand one stable `SimIssue` into cause, impact, evidence, and suggested actions. |
| [`format_report_for_agent`](format_report_for_agent.md) | Function | Compatibility name that delegates to the single Agent result renderer and accepts no style parameter. |
| [`format_result_for_agent`](format_result_for_agent.md) | Function | Format any public validation result and accept no style parameter. |
| [`format_error_for_agent`](format_error_for_agent.md) | Function | Format a structured public KinCheckAPI error for an Agent. |
| [`list_executable_fixes`](list_executable_fixes.md) | Function | Return fixes that a public API can execute safely; v0.5.0 currently always returns an empty tuple. |
| [`write_report`](write_report.md) | Function | Write a complete `DiagnosticReport` as deterministic JSON. |

## Module Rules

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.
