# `IKSolution`

## API Definition

```python
@dataclass(frozen=True)
class IKSolution:
    joint_positions: Mapping[str, float]
    initial_joint_positions: Mapping[str, float]
    position_error_m: float
    orientation_error_rad: float
    residual_norm: float
    iterations: int
    seed_index: int
    status: Literal['converged', 'limit_hit', 'singular', 'stalled', 'iteration_limit']
    within_limits: bool
    jacobian_rank: int
    reference_rank: int
    singular_values: tuple[float, ...]
    residuals: tuple[ConstraintResidual, ...]
    issues: tuple[SimIssue, ...]
```

Source: `src/kincheckapi/kinematics_ik.py`.

## Import

```python
from kincheckapi.kinematics import IKSolution
```

## Purpose

One evaluated seed, including the last state of an unsuccessful search.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `joint_positions` | `Mapping[str, float]` | required | Joint positions keyed by stable ID; radians for rotation and metres for translation. |
| `initial_joint_positions` | `Mapping[str, float]` | required | Public input or data field `initial_joint_positions`. |
| `position_error_m` | `float` | required | `position_error_m` in metres; finite. |
| `orientation_error_rad` | `float` | required | `orientation_error_rad` in radians; finite. |
| `residual_norm` | `float` | required | Public input or data field `residual_norm`. |
| `iterations` | `int` | required | Public input or data field `iterations`. |
| `seed_index` | `int` | required | Public input or data field `seed_index`. |
| `status` | `Literal['converged', 'limit_hit', 'singular', 'stalled', 'iteration_limit']` | required | Structured status interpreted according to the stable values for the result type. |
| `within_limits` | `bool` | required | Public input or data field `within_limits`. |
| `jacobian_rank` | `int` | required | Public input or data field `jacobian_rank`. |
| `reference_rank` | `int` | required | Public input or data field `reference_rank`. |
| `singular_values` | `tuple[float, ...]` | `()` | Public input or data field `singular_values`. |
| `residuals` | `tuple[ConstraintResidual, ...]` | `()` | Public input or data field `residuals`. |
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
