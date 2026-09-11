# `compute_jacobian`

## API Definition

```python
compute_jacobian(*, assembly: AssemblyModel, joint_positions: Mapping[str, float], target_component_id: str | None = None, target_connector_id: str | None = None, options: JacobianOptions | None = None) -> JacobianResult
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics import compute_jacobian
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

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
