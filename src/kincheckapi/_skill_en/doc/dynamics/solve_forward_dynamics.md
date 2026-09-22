# `solve_forward_dynamics`

## API Definition

```python
solve_forward_dynamics(*, model: kincheckapi.physics_types.DynamicsModel, request: kincheckapi.dynamic_types.ForwardDynamicsRequest) -> kincheckapi.dynamic_types.ForwardDynamicsResult
```

Source: `src/kincheckapi/dynamic_solver.py`.

## Import

```python
from kincheckapi.dynamics import solve_forward_dynamics
```

## Purpose

Integrate a finite-actuator scalar tree and retain energy evidence.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | required | Public input or data field `model`. |
| `request` | `kincheckapi.dynamic_types.ForwardDynamicsRequest` | required | Public input or data field `request`. |

## Returns and Failures

Returns `ForwardDynamicsResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
