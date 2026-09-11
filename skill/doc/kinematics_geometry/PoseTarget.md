# `PoseTarget`

## API Definition

```python
@dataclass(frozen=True)
class PoseTarget:
    component_id: str
    pose: Pose
    connector_id: str | None
    position_tolerance_m: float | None
    orientation_tolerance_rad: float | None
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import PoseTarget
```

## Purpose

PoseTarget(*, component_id: 'str', pose: 'Pose', connector_id: 'str | None' = None, position_tolerance_m: 'float | None' = None, orientation_tolerance_rad: 'float | None' = None)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `component_id` | `str` | required | Stable, resolvable component ID. |
| `pose` | `Pose` | required | Public input or data field `pose`. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |
| `position_tolerance_m` | `float | None` | `None` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float | None` | `None` | `orientation_tolerance_rad` in radians; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
