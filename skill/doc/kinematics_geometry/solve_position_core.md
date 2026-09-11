# `solve_position_core`

## API Definition

```python
solve_position_core(*, assembly: AssemblyModel, joint_positions: Optional[Mapping[str, float]] = None, pose_targets: Sequence[PoseTarget] = (), options: PositionSolveOptions | None = None) -> tuple[str, typing.Mapping[str, float], typing.Mapping[str, Pose], tuple[ConstraintResidual, ...], tuple[SimIssue, ...]]
```

Source: `src/kincheckapi/kinematics_geometry.py`.

## Import

```python
from kincheckapi.kinematics_geometry import solve_position_core
```

## Purpose

Solve one authored assembly pose and return backend-neutral records.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_positions` | `Optional[Mapping[str, float]]` | `None` | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `pose_targets` | `Sequence[PoseTarget]` | `()` | Public input or data field `pose_targets`. |
| `options` | `PositionSolveOptions | None` | `None` | Public solve or analysis options; record the effective thresholds. |

## Returns and Failures

Returns `tuple[str, Mapping[str, float], Mapping[str, Pose], tuple[ConstraintResidual, ...], tuple[SimIssue, ...]]`.

## Module Constraints

- These are low-level backend-independent primitives; prefer `kincheckapi.kinematics` for normal tasks.
- Input poses, joint positions, step sizes, and tolerances must be finite and use SI units.
- Historical `__all__` entries beginning with an underscore remain internal and are not part of this skill contract.

## Related Documentation

- [`Low-Level Kinematic Geometry`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
