# `compute_jacobian`

## API Definition

```python
compute_jacobian(*, assembly: AssemblyModel, joint_positions: Mapping[str, float], target_component_id: str | None = None, target_connector_id: str | None = None, options: JacobianOptions | None = None) -> JacobianResult
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import compute_jacobian
```

## Purpose

Compute a backend-independent six-dimensional finite-difference Jacobian for a component or connector at given joint positions.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_positions` | `Mapping[str, float]` | required | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `target_component_id` | `str | None` | `None` | Component ID used as a geometric or kinematic target. |
| `target_connector_id` | `str | None` | `None` | Optional target connector ID; omission targets the component frame. |
| `options` | `JacobianOptions | None` | `None` | Public solve or analysis options; record the effective thresholds. |

## Returns and Failures

Returns `JacobianResult`.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
