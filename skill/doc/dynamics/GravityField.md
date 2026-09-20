# `GravityField`

## API Definition

```python
@dataclass(frozen=True)
class GravityField:
    acceleration_m_s2: tuple[float, float, float]
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import GravityField
```

## Purpose

GravityField(*, acceleration_m_s2: 'tuple[float, float, float]')

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `acceleration_m_s2` | `tuple[float, float, float]` | required | `acceleration_m_s2` in m/s^2; finite. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
