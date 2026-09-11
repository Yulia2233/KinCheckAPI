# `BackendFailure`

## API Definition

```python
@dataclass(frozen=True)
class BackendFailure:
    backend_id: str
    operation: str
    native_error_type: str
    native_message: str
    backend_version: str | None
    native_error_code: str | int | None
    failure_time_s: float | None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import BackendFailure
```

## Purpose

Sanitized evidence copied from a private calculation backend.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `backend_id` | `str` | required | Stable, resolvable `backend_id`. |
| `operation` | `str` | required | Public input or data field `operation`. |
| `native_error_type` | `str` | required | Public input or data field `native_error_type`. |
| `native_message` | `str` | required | Public input or data field `native_message`. |
| `backend_version` | `str | None` | `None` | Public input or data field `backend_version`. |
| `native_error_code` | `str | int | None` | `None` | Public input or data field `native_error_code`. |
| `failure_time_s` | `float | None` | `None` | `failure_time_s` in seconds; finite. |

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
