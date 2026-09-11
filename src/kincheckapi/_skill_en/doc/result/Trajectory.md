# `Trajectory`

## API Definition

```python
@dataclass(frozen=True)
class Trajectory:
    component_id: str
    times_s: tuple[float, ...]
    poses: tuple[Pose, ...]
    connector_id: str | None
    linear_velocities_m_s: tuple[tuple[float, float, float], ...] | None
    angular_velocities_rad_s: tuple[tuple[float, float, float], ...] | None
    linear_accelerations_m_s2: tuple[tuple[float, float, float], ...] | None
    angular_accelerations_rad_s2: tuple[tuple[float, float, float], ...] | None
```

Source: `src/kincheckapi/result.py`.

## Import

```python
from kincheckapi.result import Trajectory
```

## Purpose

Rigid-body trajectory for a component or one of its connectors.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `times_s` | `tuple[float, ...]` | required | `times_s` in seconds; finite. |
| `poses` | `tuple[Pose, ...]` | required | Public input or data field `poses`. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |
| `linear_velocities_m_s` | `tuple[tuple[float, float, float], ...] | None` | `None` | `linear_velocities_m_s` in m/s; finite. |
| `angular_velocities_rad_s` | `tuple[tuple[float, float, float], ...] | None` | `None` | `angular_velocities_rad_s` in rad/s; finite. |
| `linear_accelerations_m_s2` | `tuple[tuple[float, float, float], ...] | None` | `None` | `linear_accelerations_m_s2` in m/s^2; finite. |
| `angular_accelerations_rad_s2` | `tuple[tuple[float, float, float], ...] | None` | `None` | Public input or data field `angular_accelerations_rad_s2`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Read only objects and samples actually recorded in MotionResult; never infer a pass from empty results.
- Query times must lie within the result range, and interpolated evidence must retain the original sampling range.
- Inspect status, sample count, and issues before using trajectories, residuals, or events.

## Related Documentation

- [`Result Models and Queries`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
