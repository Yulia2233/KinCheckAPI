# `DynamicState`

## API Definition

```python
@dataclass(frozen=True)
class DynamicState:
    joint_id: str
    position: float
    velocity: float
    acceleration: float
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import DynamicState
```

## Purpose

One prescribed scalar joint state at an instant. Revolute values use rad/rad/s/rad/s2 and prismatic values use m/m/s/m/s2 according to the referenced Joint type.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `position` | `float` | required | Public input or data field `position`. |
| `velocity` | `float` | `0.0` | Public input or data field `velocity`. |
| `acceleration` | `float` | `0.0` | Public input or data field `acceleration`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
