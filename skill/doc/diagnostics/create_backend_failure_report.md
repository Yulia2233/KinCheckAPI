# `create_backend_failure_report`

## API Definition

```python
create_backend_failure_report(*, scenario: Any, cause: BaseException, partial_result: Any = None) -> DiagnosticReport
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import create_backend_failure_report
```

## Purpose

Sanitize an unknown backend exception and optional partial result into a stable `DiagnosticReport`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Any` | required | An immutable `Scenario` bound to an assembly definition. |
| `cause` | `BaseException` | required | Public input or data field `cause`. |
| `partial_result` | `Any` | `None` | Public input or data field `partial_result`. |

## Returns and Failures

Returns `DiagnosticReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
