# `check_mass_properties`

## API Definition

```python
check_mass_properties(*, model: kincheckapi.physics_types.DynamicsModel) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/physics_mass.py`.

## Import

```python
from kincheckapi.dynamics import check_mass_properties
```

## Purpose

Recompute occurrence transport and aggregation to detect frame/source drift.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | required | Public input or data field `model`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
