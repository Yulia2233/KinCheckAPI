# `solve_position`

## API Definition

```python
solve_position(*, assembly: AssemblyModel, joint_positions: Optional[Mapping[str, float]] = None, pose_targets: Sequence[PoseTarget] = (), options: Union[PositionSolveOptions, Mapping[str, Any], NoneType] = None) -> PositionResult
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import solve_position
```

## Purpose

Solve one kinematic state without starting a time-domain backend.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_positions` | `Optional[Mapping[str, float]]` | `None` | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `pose_targets` | `Sequence[PoseTarget]` | `()` | Public input or data field `pose_targets`. |
| `options` | `Union[PositionSolveOptions, Mapping[str, Any], NoneType]` | `None` | Public solve or analysis options; record the effective thresholds. |

## Returns and Failures

Returns `PositionResult`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
