# `forward_component_poses`

## API Definition

```python
forward_component_poses(assembly: AssemblyModel, joint_positions: Mapping[str, float]) -> Mapping[str, Pose]
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import forward_component_poses
```

## Purpose

Propagate world poses for all components from the assembly tree and joint positions.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_positions` | `Mapping[str, float]` | required | Joint positions keyed by stable ID; radians for rotation and metres for translation. |

## Returns and Failures

Returns `Mapping[str, Pose]`.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
