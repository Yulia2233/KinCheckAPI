# `ValidationResult`

## API Definition

```python
@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[SimIssue, ...]
    operation: str
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import ValidationResult
```

## Purpose

Aggregated validation outcome; validation itself never fails fast.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |
| `operation` | `str` | `'validate'` | Public input or data field `operation`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.
- `passed` is derived from the absence of error issues; validation aggregates issues instead of failing fast.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
