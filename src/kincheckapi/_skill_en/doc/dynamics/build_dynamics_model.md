# `build_dynamics_model`

## API Definition

```python
build_dynamics_model(*, assembly: AssemblyModel, manifest: kincheckapi.physics_types.PhysicsManifest | None = None, component_properties: Optional[Mapping[str, kincheckapi.physics_types.RigidBodyProperties]] = None, occurrence_components: Optional[Mapping[str, str]] = None, payloads: Sequence[kincheckapi.physics_types.Payload] = ()) -> kincheckapi.physics_types.DynamicsModel
```

Source: `src/kincheckapi/physics_mass.py`.

## Import

```python
from kincheckapi.dynamics import build_dynamics_model
```

## Purpose

Bind complete CAD occurrence coverage OR explicit component-frame measurements.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `manifest` | `kincheckapi.physics_types.PhysicsManifest | None` | `None` | Public input or data field `manifest`. |
| `component_properties` | `Optional[Mapping[str, kincheckapi.physics_types.RigidBodyProperties]]` | `None` | Public input or data field `component_properties`. |
| `occurrence_components` | `Optional[Mapping[str, str]]` | `None` | Public input or data field `occurrence_components`. |
| `payloads` | `Sequence[kincheckapi.physics_types.Payload]` | `()` | Public input or data field `payloads`. |

## Returns and Failures

Returns `DynamicsModel`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Kinematic results cannot support force, torque, contact force, impact, fatigue, or vibration claims.
- Inverse/forward dynamics, contact response, structural analysis, vibration and fatigue are not implemented.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
