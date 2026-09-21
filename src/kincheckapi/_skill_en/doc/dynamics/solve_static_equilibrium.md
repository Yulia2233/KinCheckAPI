# `solve_static_equilibrium`

## API Definition

```python
solve_static_equilibrium(*, model: kincheckapi.physics_types.DynamicsModel, request: kincheckapi.physics_types.StaticRequest) -> kincheckapi.physics_types.StaticResult
```

Source: `src/kincheckapi/statics.py`.

## Import

```python
from kincheckapi.dynamics import solve_static_equilibrium
```

## Purpose

Balance a given tree pose. Holding effort acts on B relative to A. Wrenches are world-expressed, force on the named receiver, moment about the reported reference point. Only locked/hold scalar DOFs can supply effort.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | required | Public input or data field `model`. |
| `request` | `kincheckapi.physics_types.StaticRequest` | required | Public input or data field `request`. |

## Returns and Failures

Returns `StaticResult`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
