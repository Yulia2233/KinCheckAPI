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
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
