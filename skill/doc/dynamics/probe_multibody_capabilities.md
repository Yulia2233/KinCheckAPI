# `probe_multibody_capabilities`

## API Definition

```python
probe_multibody_capabilities(*, scenario: kincheckapi.dynamics_v07.RigidDynamicsScenario | None, operation: str = 'solve_multibody_dynamics') -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import probe_multibody_capabilities
```

## Purpose

Execute the public operation `probe_multibody_capabilities`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `kincheckapi.dynamics_v07.RigidDynamicsScenario | None` | required | An immutable `Scenario` bound to an assembly definition. |
| `operation` | `str` | `'solve_multibody_dynamics'` | Public input or data field `operation`. |

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
