# `detect_limit_events`

## API Definition

```python
detect_limit_events(*, assembly: AssemblyModel, joint_trajectories: Sequence[JointTrajectory], tolerance: float = 1e-09) -> tuple[LimitEvent, ...]
```

Source: `src/kincheckapi/kinematics_limits.py`.

## Import

```python
from kincheckapi.kinematics_limits import detect_limit_events
```

## Purpose

Find the first reached or exceeded event for each modeled joint-limit side from actual trajectories.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `assembly` | `AssemblyModel` | required | The `AssemblyModel` to construct, validate, solve, or export. |
| `joint_trajectories` | `Sequence[JointTrajectory]` | required | Public input or data field `joint_trajectories`. |
| `tolerance` | `float` | `1e-09` | Public input or data field `tolerance`. |

## Returns and Failures

Returns `tuple[LimitEvent, ...]`.

## Module Constraints

- Event detection consumes actual joint trajectories and limits authored in the assembly.
- Missing limits or trajectories produce no events and do not establish a limit-check pass.
- Tolerance must be finite and non-negative.

## Related Documentation

- [`Joint-Limit Events`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
