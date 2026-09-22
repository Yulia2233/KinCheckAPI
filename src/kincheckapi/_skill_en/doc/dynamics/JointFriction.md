# `JointFriction`

## API Definition

```python
@dataclass(frozen=True)
class JointFriction:
    joint_id: str
    coulomb_coefficient: float
    viscous_coefficient: float
    stiction_force: float
    zero_velocity_tolerance: float
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import JointFriction
```

## Purpose

JointFriction(*, joint_id: 'str', coulomb_coefficient: 'float' = 0.0, viscous_coefficient: 'float' = 0.0, stiction_force: 'float' = 0.0, zero_velocity_tolerance: 'float' = 1e-09)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `coulomb_coefficient` | `float` | `0.0` | Public input or data field `coulomb_coefficient`. |
| `viscous_coefficient` | `float` | `0.0` | Public input or data field `viscous_coefficient`. |
| `stiction_force` | `float` | `0.0` | Public input or data field `stiction_force`. |
| `zero_velocity_tolerance` | `float` | `1e-09` | Public input or data field `zero_velocity_tolerance`. |

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
