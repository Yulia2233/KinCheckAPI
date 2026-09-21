# `measure_mass_properties`

## API Definition

```python
measure_mass_properties(*, brep: bytes | str | pathlib.Path, material: kincheckapi.physics_types.PhysicsMaterial, definition_id: str, frame_id: str | None = None) -> kincheckapi.physics_types.RigidBodyProperties
```

Source: `src/kincheckapi/physics_mass.py`.

## Import

```python
from kincheckapi.dynamics import measure_mass_properties
```

## Purpose

Integrate one validated closed BREP solid in mm with uniform explicit density. OCCT MatrixOfInertia is already about the volume centroid and has units mm^5. CAD is optional until this entry point is called. No mesh/default mass fallback.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `brep` | `bytes | str | pathlib.Path` | required | Public input or data field `brep`. |
| `material` | `kincheckapi.physics_types.PhysicsMaterial` | required | Public input or data field `material`. |
| `definition_id` | `str` | required | Stable, resolvable `definition_id`. |
| `frame_id` | `str | None` | `None` | Stable, resolvable `frame_id`. |

## Returns and Failures

Returns `RigidBodyProperties`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; contact response, impact, structural stress, vibration, and fatigue remain outside the capability contract.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
