# `format_error_for_agent`

## API Definition

```python
format_error_for_agent(*, error: Any) -> str
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import format_error_for_agent
```

## Purpose

Format a structured public KinCheckAPI error for an Agent.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `error` | `Any` | required | Public input or data field `error`. |

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
