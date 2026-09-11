# `read_component_pose`

## API Definition

```python
read_component_pose(*, motion_result: MotionResult, component_id: str, time_s: float) -> Pose
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import read_component_pose
```

## Purpose

Read or interpolate a component world pose at a specified time.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |

## Returns and Failures

Returns `Pose`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
