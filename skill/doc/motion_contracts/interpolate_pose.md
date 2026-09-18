# `interpolate_pose`

## API Definition

```python
interpolate_pose(*, first: Pose, second: Pose, fraction: float) -> Pose
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import interpolate_pose
```

## Purpose

Interpolate position linearly and orientation with shortest-arc SLERP.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `first` | `Pose` | required | Public input or data field `first`. |
| `second` | `Pose` | required | Public input or data field `second`. |
| `fraction` | `float` | required | Public input or data field `fraction`. |

## Returns and Failures

Returns `Pose`.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
