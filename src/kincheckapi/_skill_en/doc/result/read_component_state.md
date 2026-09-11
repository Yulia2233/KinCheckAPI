# `read_component_state`

## API Definition

```python
read_component_state(*, motion_result: MotionResult, component_id: str, time_s: float) -> ComponentState
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import read_component_state
```

## Purpose

Read a component world pose and the available linear and angular motion values.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |

## Returns and Failures

Returns `ComponentState`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
