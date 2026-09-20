# `ContactRegion`

## API Definition

```python
@dataclass(frozen=True)
class ContactRegion:
    occurrence_a: str
    occurrence_b: str
    interface_a: str
    interface_b: str
    lower_m: tuple[float, float, float]
    upper_m: tuple[float, float, float]
    minimum_gap_m: float
    maximum_gap_m: float
    normal_a: tuple[float, float, float]
    purpose: str
    required_connection: bool
```

Source: `src/kincheckapi/physics_geometry.py`.

## Import

```python
from kincheckapi.dynamics import ContactRegion
```

## Purpose

Allowed local region in occurrence_a's definition frame, in SI metres. Both named interfaces must resolve to recorded topology. Every closest-point witness must lie inside the region; interpenetrating solids always fail. An ideal clearance fit is a geometric relation, not proof of load sharing.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `occurrence_a` | `str` | required | Public input or data field `occurrence_a`. |
| `occurrence_b` | `str` | required | Public input or data field `occurrence_b`. |
| `interface_a` | `str` | required | Public input or data field `interface_a`. |
| `interface_b` | `str` | required | Public input or data field `interface_b`. |
| `lower_m` | `tuple[float, float, float]` | required | `lower_m` in metres; finite. |
| `upper_m` | `tuple[float, float, float]` | required | `upper_m` in metres; finite. |
| `minimum_gap_m` | `float` | `0.0` | `minimum_gap_m` in metres; finite. |
| `maximum_gap_m` | `float` | `0.0002` | `maximum_gap_m` in metres; finite. |
| `normal_a` | `tuple[float, float, float]` | `(0.0, 0.0, 1.0)` | Public input or data field `normal_a`. |
| `purpose` | `str` | `'ideal mechanical interface'` | Public input or data field `purpose`. |
| `required_connection` | `bool` | `True` | Public input or data field `required_connection`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
