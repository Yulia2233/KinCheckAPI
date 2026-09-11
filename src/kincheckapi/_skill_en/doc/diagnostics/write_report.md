# `write_report`

## API Definition

```python
write_report(*, report: DiagnosticReport, path: str | pathlib.Path) -> None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import write_report
```

## Purpose

Write a complete `DiagnosticReport` as deterministic JSON.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `report` | `DiagnosticReport` | required | Public input or data field `report`. |
| `path` | `str | pathlib.Path` | required | Input or output path as described by the operation. |

## Returns and Failures

Returns `None`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
