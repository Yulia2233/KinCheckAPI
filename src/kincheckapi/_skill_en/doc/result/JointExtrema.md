# `JointExtrema`

## API Definition

```python
@dataclass(frozen=True)
class JointExtrema:
    joint_id: str
    minimum_position: float
    maximum_position: float
    maximum_absolute_velocity: float
    maximum_absolute_acceleration: float
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import JointExtrema
```

## Purpose

JointExtrema(*, joint_id: 'str', minimum_position: 'float', maximum_position: 'float', maximum_absolute_velocity: 'float', maximum_absolute_acceleration: 'float')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `minimum_position` | `float` | required | Public input or data field `minimum_position`. |
| `maximum_position` | `float` | required | Public input or data field `maximum_position`. |
| `maximum_absolute_velocity` | `float` | required | Public input or data field `maximum_absolute_velocity`. |
| `maximum_absolute_acceleration` | `float` | required | Public input or data field `maximum_absolute_acceleration`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
