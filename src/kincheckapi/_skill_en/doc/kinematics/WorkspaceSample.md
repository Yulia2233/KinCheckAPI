# `WorkspaceSample`

## API Definition

```python
@dataclass(frozen=True)
class WorkspaceSample:
    joint_positions: Mapping[str, float]
    reachable: bool
    pose: Pose | None
    residual_m: float | None
    orientation_residual_rad: float | None
    singularity_status: str | None
    jacobian_rank: int | None
    minimum_singular_value: float | None
    condition_number: float | None
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics_analysis.py`.

## Import

```python
from kincheckapi.kinematics import WorkspaceSample
```

## Purpose

WorkspaceSample(*, joint_positions: 'Mapping[str, float]', reachable: 'bool', pose: 'Pose | None' = None, residual_m: 'float | None' = None, orientation_residual_rad: 'float | None' = None, singularity_status: 'str | None' = None, jacobian_rank: 'int | None' = None, minimum_singular_value: 'float | None' = None, condition_number: 'float | None' = None, issues: 'tuple[SimIssue, ...]' = ())

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_positions` | `Mapping[str, float]` | required | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `reachable` | `bool` | required | Public input or data field `reachable`. |
| `pose` | `Pose | None` | `None` | Public input or data field `pose`. |
| `residual_m` | `float | None` | `None` | `residual_m` in metres; finite. |
| `orientation_residual_rad` | `float | None` | `None` | `orientation_residual_rad` in radians; finite. |
| `singularity_status` | `str | None` | `None` | Public input or data field `singularity_status`. |
| `jacobian_rank` | `int | None` | `None` | Public input or data field `jacobian_rank`. |
| `minimum_singular_value` | `float | None` | `None` | Public input or data field `minimum_singular_value`. |
| `condition_number` | `float | None` | `None` | Public input or data field `condition_number`. |
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
