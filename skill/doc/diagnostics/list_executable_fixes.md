# `list_executable_fixes`

## API Definition

```python
list_executable_fixes(*, report: DiagnosticReport) -> tuple[Fix, ...]
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import list_executable_fixes
```

## Purpose

Return fixes that a public API can execute safely; v0.5.0 currently always returns an empty tuple.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `report` | `DiagnosticReport` | required | Public input or data field `report`. |

## Returns and Failures

Returns `tuple[Fix, ...]`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.
- When no executable fix exists, this returns `()`; callers must not invent changes from that result.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
