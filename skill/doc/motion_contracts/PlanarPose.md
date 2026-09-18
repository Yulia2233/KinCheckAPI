# `PlanarPose`

## API Definition

```python
@dataclass(frozen=True)
class PlanarPose:
    time_s: float
    x_m: float
    y_m: float
    yaw_rad: float
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import PlanarPose
```

## Purpose

PlanarPose(*, time_s: 'float', x_m: 'float', y_m: 'float', yaw_rad: 'float')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `x_m` | `float` | required | `x_m` in metres; finite. |
| `y_m` | `float` | required | `y_m` in metres; finite. |
| `yaw_rad` | `float` | required | `yaw_rad` in radians; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
