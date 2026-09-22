# `validate_physics_conversion`

## API Definition

```python
validate_physics_conversion(*, model: kincheckapi.physics_types.DynamicsModel, compilation: kincheckapi.physics_backend.DynamicsCompilation | None = None) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/physics_backend.py`.

## Import

```python
from kincheckapi.dynamics import validate_physics_conversion
```

## Purpose

Audit definition→occurrence→rigid-group→compiled-body conservation.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | required | Public input or data field `model`. |
| `compilation` | `kincheckapi.physics_backend.DynamicsCompilation | None` | `None` | Public input or data field `compilation`. |

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
