# `compile_dynamics_model`

## API Definition

```python
compile_dynamics_model(*, model: kincheckapi.physics_types.DynamicsModel) -> kincheckapi.physics_backend.DynamicsCompilation
```

Source: `src/kincheckapi/physics_backend.py`.

## Import

```python
from kincheckapi.dynamics import compile_dynamics_model
```

## Purpose

Compile the actual assembly with explicit m/c/I for every rigid group.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `kincheckapi.physics_types.DynamicsModel` | required | Public input or data field `model`. |

## Returns and Failures

Returns `DynamicsCompilation`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
