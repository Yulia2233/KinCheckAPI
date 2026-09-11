# `Pose`

## API Definition

```python
@dataclass(frozen=True)
class Pose:
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
```

Source: `src/kincheckapi/pose.py`.

## Import

```python
from kincheckapi.assembly import Pose
```

## Purpose

Rigid transform expressed in SI units with an xyzw quaternion.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `position_m` | `tuple[float, float, float]` | `(0.0, 0.0, 0.0)` | `position_m` in metres; finite. |
| `orientation_xyzw` | `tuple[float, float, float, float]` | `(0.0, 0.0, 0.0, 1.0)` | Public input or data field `orientation_xyzw`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- The data model is immutable; capture the return value of every `add_*`, `set_*`, and `ground_*` call.
- IDs must be stable and unique, and all part, component, joint, connector, and constraint references must resolve.
- Run `validate_assembly()` and `validate_topology()` before solving.

## Related Documentation

- [`Assembly Model and Topology`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
