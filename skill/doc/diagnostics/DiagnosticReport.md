# `DiagnosticReport`

## API Definition

```python
@dataclass(frozen=True)
class DiagnosticReport:
    issues: tuple[SimIssue, ...]
    failure_time_s: float | None
    last_valid_result: Any
    backend_failure: BackendFailure | None
    metadata: Mapping[str, Any]
    operation: str
    status: Optional[Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']]
    traceback: str | None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import DiagnosticReport
```

## Purpose

Complete diagnostic context attached to a public KinCheckAPI error.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `failure_time_s` | `float | None` | `None` | `failure_time_s` in seconds; finite. |
| `last_valid_result` | `Any` | `None` | Public input or data field `last_valid_result`. |
| `backend_failure` | `BackendFailure | None` | `None` | Public input or data field `backend_failure`. |
| `metadata` | `Mapping[str, Any]` | default_factory | Additional read-only structured metadata. |
| `operation` | `str` | `'diagnose'` | Public input or data field `operation`. |
| `status` | `Optional[Literal['passed', 'failed', 'partial', 'capability_failed', 'validation_failed']]` | `None` | Structured status interpreted according to the stable values for the result type. |
| `traceback` | `str | None` | `None` | Public input or data field `traceback`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
