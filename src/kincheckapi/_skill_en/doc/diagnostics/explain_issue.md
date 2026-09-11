# `explain_issue`

## API Definition

```python
explain_issue(*, issue: SimIssue) -> IssueExplanation
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import explain_issue
```

## Purpose

Expand one stable `SimIssue` into cause, impact, evidence, and suggested actions.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `issue` | `SimIssue` | required | Public input or data field `issue`. |

## Returns and Failures

Returns `IssueExplanation`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
