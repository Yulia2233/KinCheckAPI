# `probe_dynamics_capabilities`

## API Definition

```python
probe_dynamics_capabilities(*, model: kincheckapi.physics_types.DynamicsModel | None, operation: str, backend: str | None = None) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/statics.py`.

## Import

```python
from kincheckapi.dynamics import probe_dynamics_capabilities
```

## Purpose

Probe the requested operation/topology/data/backend combination.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel | None` | required | Public input or data field `model`. |
| `operation` | `str` | required | Public input or data field `operation`. |
| `backend` | `str | None` | `None` | Public input or data field `backend`. |

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
