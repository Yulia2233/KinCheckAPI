# `ScenarioValidationError`

## API Definition

```python
class ScenarioValidationError(KinCheckError): ...

ScenarioValidationError(*, code: 'str', message: 'str | None' = None, report: 'DiagnosticReport | ValidationResult | None' = None, object_ids: 'Sequence[str]' = (), source_paths: 'Sequence[str]' = (), suggested_actions: 'Sequence[str]' = (), details: 'Mapping[str, Any] | None' = None, operation: 'str | None' = None, status: 'str | None' = None) -> 'None'
```

Source: `src/kincheckapi/errors.py`.

## Import

```python
from kincheckapi.errors import ScenarioValidationError
```

## Purpose

Raised when Scenario time, state, drivers, or object references are invalid.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `code` | `str` | required | Public input or data field `code`. |
| `message` | `str | None` | `None` | Public input or data field `message`. |
| `report` | `DiagnosticReport | ValidationResult | None` | `None` | Public input or data field `report`. |
| `object_ids` | `Sequence[str]` | `()` | Explicitly specified `object_ids` collection. |
| `source_paths` | `Sequence[str]` | `()` | Public input or data field `source_paths`. |
| `suggested_actions` | `Sequence[str]` | `()` | Public input or data field `suggested_actions`. |
| `details` | `Optional[Mapping[str, Any]]` | `None` | Public input or data field `details`. |
| `operation` | `str | None` | `None` | Public input or data field `operation`. |
| `status` | `str | None` | `None` | Structured status interpreted according to the stable values for the result type. |

## Returns and Failures

Constructs a public domain exception. After catching it, read `code`, `report`, and structured context instead of matching free text.

## Module Constraints

- Catch `KinCheckError` for expected domain failures, then narrow to subclasses when needed.
- Preserve `code`, `report`, `object_ids`, `source_paths`, and `suggested_actions`.
- Do not choose repair behavior by matching exception message text.

## Related Documentation

- [`Public Exceptions`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
