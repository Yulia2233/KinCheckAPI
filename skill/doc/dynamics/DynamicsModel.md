# `DynamicsModel`

## API Definition

```python
@dataclass(frozen=True)
class DynamicsModel:
    assembly: AssemblyModel
    component_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    body_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
    occurrence_components: Mapping[str, str]
    manifest: kincheckapi.physics_types.PhysicsManifest | None
    payloads: tuple[kincheckapi.physics_types.Payload, ...]
    base_component_properties: Mapping[str, kincheckapi.physics_types.RigidBodyProperties]
```

Source: `src/kincheckapi/physics_types.py`.

## Import

```python
from kincheckapi.dynamics import DynamicsModel
```

## Purpose

DynamicsModel(*, assembly: 'AssemblyModel', component_properties: 'Mapping[str, RigidBodyProperties]', body_properties: 'Mapping[str, RigidBodyProperties]', occurrence_components: 'Mapping[str, str]', manifest: 'PhysicsManifest | None' = None, payloads: 'tuple[Payload, ...]' = (), base_component_properties: 'Mapping[str, RigidBodyProperties]' = <factory>)

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `component_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | required | Public input or data field `component_properties`. |
| `body_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | required | Public input or data field `body_properties`. |
| `occurrence_components` | `Mapping[str, str]` | required | Public input or data field `occurrence_components`. |
| `manifest` | `kincheckapi.physics_types.PhysicsManifest | None` | `None` | Public input or data field `manifest`. |
| `payloads` | `tuple[kincheckapi.physics_types.Payload, ...]` | `()` | Public input or data field `payloads`. |
| `base_component_properties` | `Mapping[str, kincheckapi.physics_types.RigidBodyProperties]` | default_factory | Public input or data field `base_component_properties`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
