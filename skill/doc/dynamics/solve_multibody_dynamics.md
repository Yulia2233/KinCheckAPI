# `solve_multibody_dynamics`

## API Definition

```python
solve_multibody_dynamics(*, scenario: kincheckapi.dynamics_v07.RigidDynamicsScenario, reaction_request: kincheckapi.dynamics_v07.ReactionRequest | None = None) -> kincheckapi.dynamics_v07.MultibodyResult
```

Source: `src/kincheckapi/dynamics_v07.py`.

## Import

```python
from kincheckapi.dynamics import solve_multibody_dynamics
```

## Purpose

Solve the specified kinematic problem: `solve_multibody_dynamics`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `kincheckapi.dynamics_v07.RigidDynamicsScenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `reaction_request` | `kincheckapi.dynamics_v07.ReactionRequest | None` | `None` | Public input or data field `reaction_request`. |

## Returns and Failures

Returns `MultibodyResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
