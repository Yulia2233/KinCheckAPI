# `measure_package_physics`

## API Definition

```python
measure_package_physics(*, package_path: str | pathlib.Path, sdk_python: str | pathlib.Path | None = None) -> kincheckapi.physics_types.PhysicsManifest
```

Source: `src/kincheckapi/physics_cadir.py`.

## Import

```python
from kincheckapi.dynamics import measure_package_physics
```

## Purpose

Validate .scadpkg, integrate definitions and expand every leaf occurrence. sdk_python explicitly opts into an isolated legacy SDK reader. It never tries another interpreter after failure; actual SDK and encoding enter provenance. Supported tested readers: 2.1.3b3 canonical ticks; 2.0.4b3 legacy millimeters.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `package_path` | `str | pathlib.Path` | required | Public input or data field `package_path`. |
| `sdk_python` | `str | pathlib.Path | None` | `None` | Public input or data field `sdk_python`. |

## Returns and Failures

Returns `PhysicsManifest`.

## Module Constraints

- Use typed SI physics contracts after mass coverage and compiled inertia validation.
- Inverse/forward dynamics support scalar revolute/prismatic trees without closures, couplings, or general constraints.
- Contact capacity is a supplied-force Coulomb/pressure check; v0.7 rigid contact/impulse results must preserve contact state, momentum, energy, and convergence evidence.
- Structural meshes, stress, structural vibration, and fatigue belong to the independent FEACheckAPI; KinCheckAPI exports motion, rigid loads, reactions, and impulses only.

## Related Documentation

- [`Dynamics Namespace`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
