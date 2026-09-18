# `CoordinatedMotionProfile`

## API Definition

```python
@dataclass(frozen=True)
class CoordinatedMotionProfile:
    axes: Mapping[str, tuple[float, ...]]
    times_s: tuple[float, ...]
    position_tolerance: float
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import CoordinatedMotionProfile
```

## Purpose

Scalar joint position targets sharing one time axis.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `axes` | `Mapping[str, tuple[float, ...]]` | required | Public input or data field `axes`. |
| `times_s` | `tuple[float, ...]` | required | `times_s` in seconds; finite. |
| `position_tolerance` | `float` | `1e-06` | Public input or data field `position_tolerance`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
