# `solve_inverse_dynamics`

## API Definition

```python
solve_inverse_dynamics(*, model: kincheckapi.physics_types.DynamicsModel, request: kincheckapi.dynamic_types.DynamicRequest) -> kincheckapi.dynamic_types.InverseDynamicsResult
```

Source: `src/kincheckapi/dynamic_solver.py`.

## Import

```python
from kincheckapi.dynamics import solve_inverse_dynamics
```

## Purpose

Compute scalar joint effort for prescribed position/velocity/acceleration. The calculation is MuJoCo's inverse dynamics with explicit CADIR-derived mass/COM/inertia. It supports tree revolute/prismatic joints only.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | required | Public input or data field `model`. |
| `request` | `kincheckapi.dynamic_types.DynamicRequest` | required | Public input or data field `request`. |

## Returns and Failures

Returns `InverseDynamicsResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
