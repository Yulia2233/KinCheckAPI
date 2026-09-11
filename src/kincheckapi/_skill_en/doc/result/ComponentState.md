# `ComponentState`

## API Definition

```python
@dataclass(frozen=True)
class ComponentState:
    component_id: str
    time_s: float
    pose: Pose
    linear_velocity_m_s: tuple[float, float, float] | None
    angular_velocity_rad_s: tuple[float, float, float] | None
    linear_acceleration_m_s2: tuple[float, float, float] | None
    angular_acceleration_rad_s2: tuple[float, float, float] | None
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import ComponentState
```

## Purpose

ComponentState(*, component_id: 'str', time_s: 'float', pose: 'Pose', linear_velocity_m_s: 'Vector3 | None' = None, angular_velocity_rad_s: 'Vector3 | None' = None, linear_acceleration_m_s2: 'Vector3 | None' = None, angular_acceleration_rad_s2: 'Vector3 | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `pose` | `Pose` | required | Public input or data field `pose`. |
| `linear_velocity_m_s` | `tuple[float, float, float] | None` | `None` | `linear_velocity_m_s` in m/s; finite. |
| `angular_velocity_rad_s` | `tuple[float, float, float] | None` | `None` | `angular_velocity_rad_s` in rad/s; finite. |
| `linear_acceleration_m_s2` | `tuple[float, float, float] | None` | `None` | `linear_acceleration_m_s2` in m/s^2; finite. |
| `angular_acceleration_rad_s2` | `tuple[float, float, float] | None` | `None` | Public input or data field `angular_acceleration_rad_s2`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
