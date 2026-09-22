# `check_static_geometry`

## API Definition

```python
check_static_geometry(*, package_path: str | pathlib.Path, manifest: kincheckapi.physics_types.PhysicsManifest, occurrence_components: Mapping[str, str], component_initial_poses: Mapping[str, Pose], component_poses: Mapping[str, Pose], contacts: Sequence[kincheckapi.physics_geometry.ContactRegion] = (), free_clearance_m: float = 0.0001, guard_clearance_m: float = 0.005, guard_occurrence_ids: Sequence[str] = (), query_error_m: float = 1e-09) -> kincheckapi.physics_types.PhysicsReport
```

Source: `src/kincheckapi/physics_geometry.py`.

## Import

```python
from kincheckapi.dynamics import check_static_geometry
```

## Purpose

Check every leaf pair using exact BREP, including fixed-group internals. Broad-phase boxes only prove separation; nearby pairs use BREP distances and solid intersections. No triangle approximation is used for acceptance.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `package_path` | `str | pathlib.Path` | required | Public input or data field `package_path`. |
| `manifest` | `kincheckapi.physics_types.PhysicsManifest` | required | Public input or data field `manifest`. |
| `occurrence_components` | `Mapping[str, str]` | required | Public input or data field `occurrence_components`. |
| `component_initial_poses` | `Mapping[str, Pose]` | required | Public input or data field `component_initial_poses`. |
| `component_poses` | `Mapping[str, Pose]` | required | Public input or data field `component_poses`. |
| `contacts` | `Sequence[kincheckapi.physics_geometry.ContactRegion]` | `()` | Public input or data field `contacts`. |
| `free_clearance_m` | `float` | `0.0001` | `free_clearance_m` in metres; finite. |
| `guard_clearance_m` | `float` | `0.005` | `guard_clearance_m` in metres; finite. |
| `guard_occurrence_ids` | `Sequence[str]` | `()` | Explicitly specified `guard_occurrence_ids` collection. |
| `query_error_m` | `float` | `1e-09` | `query_error_m` in metres; finite. |

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
