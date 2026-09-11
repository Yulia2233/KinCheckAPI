# `AgentGuidance`

## API Definition

```python
@dataclass(frozen=True)
class AgentGuidance:
    operation: str
    what_happened: str | None
    possible_causes: tuple[str, ...]
    how_to_fix: tuple[str, ...]
    documentation_hint: str | None
```

Source: `src/kincheckapi/diagnostics.py`.

## Import

```python
from kincheckapi.diagnostics import AgentGuidance
```

## Purpose

Stable repair guidance associated with one public error code.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `operation` | `str` | required | Public input or data field `operation`. |
| `what_happened` | `str | None` | `None` | Public input or data field `what_happened`. |
| `possible_causes` | `tuple[str, ...]` | `()` | Public input or data field `possible_causes`. |
| `how_to_fix` | `tuple[str, ...]` | `()` | Public input or data field `how_to_fix`. |
| `documentation_hint` | `str | None` | `None` | Public input or data field `documentation_hint`. |

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
