# `InterferenceResult`

## API Definition

```python
@dataclass(frozen=True)
class InterferenceResult:
    events: tuple[InterferenceEvent, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import InterferenceResult
```

## Purpose

InterferenceResult(*, events: 'tuple[InterferenceEvent, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `events` | `tuple[InterferenceEvent, ...]` | `()` | Public input or data field `events`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
