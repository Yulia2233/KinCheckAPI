# `list_limit_events`

## API Definition

```python
list_limit_events(*, motion_result: MotionResult, joint_id: str | None = None) -> tuple[LimitEvent, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import list_limit_events
```

## Purpose

Filter and return recorded structured evidence: `list_limit_events`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `joint_id` | `str | None` | `None` | Stable, resolvable joint ID. |

## Returns and Failures

Returns `tuple[LimitEvent, ...]`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
