# `check_static_load_limits`

## API Definition

```python
check_static_load_limits(*, result: kincheckapi.physics_types.StaticResult, limits: Mapping[str, float]) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/statics.py`.

## Import

```python
from kincheckapi.dynamics import check_static_load_limits
```

## Purpose

Compare scalar holding demands to positive N/N*m ratings; no stress claim.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `result` | `kincheckapi.physics_types.StaticResult` | required | Public input or data field `result`. |
| `limits` | `Mapping[str, float]` | required | Public input or data field `limits`. |

## Returns and Failures

Returns `PhysicsReport`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
