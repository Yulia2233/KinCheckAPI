# `WorkspaceResult`

## API Definition

```python
@dataclass(frozen=True)
class WorkspaceResult:
    target: TargetReference
    samples: tuple[WorkspaceSample, ...]
    reachable_points: tuple[Pose, ...]
    bounds_m: Mapping[str, tuple[float, float]]
    reachable_fraction: float
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import WorkspaceResult
```

## Purpose

WorkspaceResult(*, target: 'TargetReference', samples: 'tuple[WorkspaceSample, ...]', reachable_points: 'tuple[Pose, ...]', bounds_m: 'Mapping[str, tuple[float, float]]', reachable_fraction: 'float', issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `target` | `TargetReference` | required | Public input or data field `target`. |
| `samples` | `tuple[WorkspaceSample, ...]` | required | Public input or data field `samples`. |
| `reachable_points` | `tuple[Pose, ...]` | required | Public input or data field `reachable_points`. |
| `bounds_m` | `Mapping[str, tuple[float, float]]` | required | `bounds_m` in metres; finite. |
| `reachable_fraction` | `float` | required | Public input or data field `reachable_fraction`. |
| `issues` | `tuple[SimIssue, ...]` | `()` | Structured issues preserving error codes, objects, and evidence. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
