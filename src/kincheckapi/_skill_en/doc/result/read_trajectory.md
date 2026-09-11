# `read_trajectory`

## API Definition

```python
read_trajectory(*, motion_result: MotionResult, component_id: str, connector_id: str | None = None) -> Trajectory
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import read_trajectory
```

## Purpose

Return a complete component or connector trajectory already recorded in the result.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |

## Returns and Failures

Returns `Trajectory`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
