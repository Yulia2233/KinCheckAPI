# `PathTarget`

## API Definition

```python
@dataclass(frozen=True)
class PathTarget:
    points_m: tuple[tuple[float, float, float], ...]
    closed: bool
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import PathTarget
```

## Purpose

Geometric polyline target. This does not prescribe timing or traversal.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `points_m` | `tuple[tuple[float, float, float], ...]` | required | `points_m` in metres; finite. |
| `closed` | `bool` | `False` | Public input or data field `closed`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
