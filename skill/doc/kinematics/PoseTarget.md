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
from kincheckapi.kinematics import PoseTarget
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

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
