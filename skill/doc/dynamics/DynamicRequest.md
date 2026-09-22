# `DynamicRequest`

## API Definition

```python
@dataclass(frozen=True)
class DynamicRequest:
    states: tuple[kincheckapi.dynamic_types.DynamicState, ...]
    gravity: kincheckapi.physics_types.GravityField
    loads: tuple[kincheckapi.physics_types.WrenchLoad, ...]
```

Source: `src/kincheckapi/dynamic_types.py`.

## Import

```python
from kincheckapi.dynamics import DynamicRequest
```

## Purpose

Inputs for one inverse-dynamics evaluation.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `states` | `tuple[kincheckapi.dynamic_types.DynamicState, ...]` | required | Public input or data field `states`. |
| `gravity` | `kincheckapi.physics_types.GravityField` | default_factory | Public input or data field `gravity`. |
| `loads` | `tuple[kincheckapi.physics_types.WrenchLoad, ...]` | `()` | Public input or data field `loads`. |

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
