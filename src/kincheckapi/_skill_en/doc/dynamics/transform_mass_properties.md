# `transform_mass_properties`

## API Definition

```python
transform_mass_properties(*, properties: kincheckapi.physics_types.RigidBodyProperties, pose: Pose, frame_id: str) -> kincheckapi.physics_types.RigidBodyProperties
```

Source: `src/kincheckapi/physics_mass.py`.

## Import

```python
from kincheckapi.dynamics import transform_mass_properties
```

## Purpose

Rigid transport; COM inertia rotates but translation adds no parallel-axis term.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `properties` | `kincheckapi.physics_types.RigidBodyProperties` | required | Public input or data field `properties`. |
| `pose` | `Pose` | required | Public input or data field `pose`. |
| `frame_id` | `str` | required | Stable, resolvable `frame_id`. |

## Returns and Failures

Returns `RigidBodyProperties`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
