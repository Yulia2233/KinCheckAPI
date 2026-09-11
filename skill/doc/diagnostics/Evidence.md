# `Evidence`

## API Definition

```python
@dataclass(frozen=True)
class Evidence:
    key: str
    actual: Any
    expected: Any
    unit: str | None
    description: str | None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import Evidence
```

## Purpose

One machine-readable fact supporting a diagnostic conclusion.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `key` | `str` | required | Public input or data field `key`. |
| `actual` | `Any` | `None` | Public input or data field `actual`. |
| `expected` | `Any` | `None` | Public input or data field `expected`. |
| `unit` | `str | None` | `None` | Public input or data field `unit`. |
| `description` | `str | None` | `None` | Public input or data field `description`. |

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
