# `create_report`

## API Definition

```python
create_report(*, assembly: Any, scenario: Any = None, motion_result: Any = None, clearance_result: Any = None, check_results: Iterable[Any] = ()) -> DiagnosticReport
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import create_report
```

## Purpose

Combine issues from assembly, Scenario, motion, geometric safety, and checks into one `DiagnosticReport`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `Any` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `scenario` | `Any` | `None` | An immutable `Scenario` bound to an assembly definition. |
| `motion_result` | `Any` | `None` | The public `MotionResult` to query or check. |
| `clearance_result` | `Any` | `None` | Public input or data field `clearance_result`. |
| `check_results` | `Iterable[Any]` | `()` | Public input or data field `check_results`. |

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
