# `list_interference_events`

## API Definition

```python
list_interference_events(*, interference_result: InterferenceResult) -> tuple[InterferenceEvent, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import list_interference_events
```

## Purpose

Filter and return recorded structured evidence: `list_interference_events`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `interference_result` | `InterferenceResult` | required | Public input or data field `interference_result`. |

## Returns and Failures

Returns `tuple[InterferenceEvent, ...]`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
