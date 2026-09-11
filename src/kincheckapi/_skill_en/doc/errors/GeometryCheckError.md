# `GeometryCheckError`

## API Definition

```python
class GeometryCheckError(MotionSolveError): ...

GeometryCheckError(*, failure_time_s: 'float | None' = None, last_valid_result: 'Any' = None, backend_failure: 'BackendFailure | None' = None, **kwargs: 'Any') -> 'None'
```

Source: `src/kincheckapi/errors.py`.

## Import

```python
from kincheckapi.errors import GeometryCheckError
```

## Purpose

Raised when interference, clearance, or motion-envelope operations fail.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `failure_time_s` | `float | None` | `None` | `failure_time_s` in seconds; finite. |
| `last_valid_result` | `Any` | `None` | Public input or data field `last_valid_result`. |
| `backend_failure` | `BackendFailure | None` | `None` | Public input or data field `backend_failure`. |
| `kwargs` | `Any` | required | Public input or data field `kwargs`. |

## Returns and Failures

Constructs a public domain exception. After catching it, read `code`, `report`, and structured context instead of matching free text.

## Module Constraints

- Catch `KinCheckError` for expected domain failures, then narrow to subclasses when needed.
- Preserve `code`, `report`, `object_ids`, `source_paths`, and `suggested_actions`.
- Do not choose repair behavior by matching exception message text.

## Related Documentation

- [`Public Exceptions`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
