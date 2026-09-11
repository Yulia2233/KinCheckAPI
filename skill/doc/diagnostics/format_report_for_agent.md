# `format_report_for_agent`

## API Definition

```python
format_report_for_agent(report: DiagnosticReport) -> str
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import format_report_for_agent
```

## Purpose

Compatibility name that delegates to the single Agent result renderer and accepts no style parameter.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `report` | `DiagnosticReport` | required | Public input or data field `report`. |

## Returns and Failures

Returns `str`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Prefer stable error codes, object IDs, source paths, and Evidence over free-text matching.
- Execute an automatic fix only when a public API defines it and its preconditions are verifiable.
- Wrap backend failures as BackendFailure; do not expose or depend on private backend objects.

## Related Documentation

- [`Structured Diagnostics`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
