# `aggregate_mass_properties`

## API Definition

```python
aggregate_mass_properties(*, properties: Sequence[kincheckapi.physics_types.RigidBodyProperties], frame_id: str) -> kincheckapi.physics_types.RigidBodyProperties
```

Source: `src/kincheckapi/physics_mass.py`.

## Import

```python
from kincheckapi.dynamics import aggregate_mass_properties
```

## Purpose

Sum every supplied physical instance using the parallel-axis theorem.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `properties` | `Sequence[kincheckapi.physics_types.RigidBodyProperties]` | required | Public input or data field `properties`. |
| `frame_id` | `str` | required | Stable, resolvable `frame_id`. |

## Returns and Failures

Returns `RigidBodyProperties`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
