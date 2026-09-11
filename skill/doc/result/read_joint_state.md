# `read_joint_state`

## API Definition

```python
read_joint_state(*, motion_result: MotionResult, joint_id: str, time_s: float) -> JointState
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import read_joint_state
```

## Purpose

Read or interpolate joint position, velocity, and acceleration at a specified time.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |

## Returns and Failures

Returns `JointState`.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
