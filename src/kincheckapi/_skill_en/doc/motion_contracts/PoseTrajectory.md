# `PoseTrajectory`

## API Definition

```python
@dataclass(frozen=True)
class PoseTrajectory:
    target: Union[TargetReference, str, Mapping[str, Any]]
    points: tuple[kincheckapi.motion_contracts.PosePoint, ...]
    interpolation: str
    position_tolerance_m: float
    orientation_tolerance_rad: float
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import PoseTrajectory
```

## Purpose

A world-frame, time-indexed acceptance target, not a Cartesian driver.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `target` | `Union[TargetReference, str, Mapping[str, Any]]` | required | Public input or data field `target`. |
| `points` | `tuple[kincheckapi.motion_contracts.PosePoint, ...]` | required | Public input or data field `points`. |
| `interpolation` | `str` | `'linear'` | Public input or data field `interpolation`. |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad` in radians; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
