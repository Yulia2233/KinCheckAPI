# `IssueExplanation`

## API Definition

```python
@dataclass(frozen=True)
class IssueExplanation:
    cause: str
    impact: str
    evidence: tuple[Evidence, ...]
    object_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    suggested_actions: tuple[str, ...]
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import IssueExplanation
```

## Purpose

Agent-facing explanation without depending on free-form exception text.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `cause` | `str` | required | Public input or data field `cause`. |
| `impact` | `str` | required | Public input or data field `impact`. |
| `evidence` | `tuple[Evidence, ...]` | required | Machine-readable evidence supporting the conclusion. |
| `object_ids` | `tuple[str, ...]` | required | Explicitly specified `object_ids` collection. |
| `source_paths` | `tuple[str, ...]` | required | Public input or data field `source_paths`. |
| `suggested_actions` | `tuple[str, ...]` | required | Public input or data field `suggested_actions`. |

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
