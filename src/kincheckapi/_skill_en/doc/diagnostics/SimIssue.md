# `SimIssue`

## API Definition

```python
@dataclass(frozen=True)
class SimIssue:
    code: str
    severity: Literal['info', 'warning', 'error']
    stage: str
    message: str
    object_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    suggested_actions: tuple[str, ...]
    failure_time_s: float | None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import SimIssue
```

## Purpose

A stable, actionable issue produced by validation or verification.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `code` | `str` | required | Public input or data field `code`. |
| `severity` | `Literal['info', 'warning', 'error']` | required | Public input or data field `severity`. |
| `stage` | `str` | required | Public input or data field `stage`. |
| `message` | `str` | required | Public input or data field `message`. |
| `object_ids` | `tuple[str, ...]` | `()` | Explicitly specified `object_ids` collection. |
| `source_paths` | `tuple[str, ...]` | `()` | Public input or data field `source_paths`. |
| `evidence` | `tuple[Evidence, ...]` | `()` | Machine-readable evidence supporting the conclusion. |
| `suggested_actions` | `tuple[str, ...]` | `()` | Public input or data field `suggested_actions`. |
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
