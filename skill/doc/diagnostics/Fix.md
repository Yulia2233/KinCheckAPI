# `Fix`

## API Definition

```python
@dataclass(frozen=True)
class Fix:
    operation: str
    target_id: str
    parameters: Mapping[str, Any]
    confidence: float
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import Fix
```

## Purpose

A deliberately small mechanical patch description.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | required | Public input or data field `operation`. |
| `target_id` | `str` | required | Stable, resolvable `target_id`. |
| `parameters` | `Mapping[str, Any]` | default_factory | Explicit parameters for the check type; do not rely on unrecorded implicit acceptance defaults. |
| `confidence` | `float` | `1.0` | Public input or data field `confidence`. |

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
