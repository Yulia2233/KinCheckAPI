# `JointState`

## API Definition

```python
@dataclass(frozen=True)
class JointState:
    joint_id: str
    time_s: float
    position: float
    velocity: float
    acceleration: float
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import JointState
```

## Purpose

One scalar joint sample in SI units (radians or metres).

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `position` | `float` | required | Public input or data field `position`. |
| `velocity` | `float` | required | Public input or data field `velocity`. |
| `acceleration` | `float` | required | Public input or data field `acceleration`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
