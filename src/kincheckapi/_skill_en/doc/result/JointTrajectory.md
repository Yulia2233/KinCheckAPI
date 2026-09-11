# `JointTrajectory`

## API Definition

```python
@dataclass(frozen=True)
class JointTrajectory:
    joint_id: str
    times_s: tuple[float, ...]
    positions: tuple[float, ...]
    velocities: tuple[float, ...]
    accelerations: tuple[float, ...]
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import JointTrajectory
```

## Purpose

Complete sampled state of one revolute or prismatic joint.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `times_s` | `tuple[float, ...]` | required | `times_s` in seconds; finite. |
| `positions` | `tuple[float, ...]` | required | Public input or data field `positions`. |
| `velocities` | `tuple[float, ...]` | required | Public input or data field `velocities`. |
| `accelerations` | `tuple[float, ...]` | required | Public input or data field `accelerations`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
