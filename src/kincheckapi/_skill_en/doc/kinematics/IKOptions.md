# `IKOptions`

## API Definition

```python
@dataclass(frozen=True)
class IKOptions:
    position_tolerance_m: float
    orientation_tolerance_rad: float
    max_iterations: int
    damping: float
    step_tolerance: float
    residual_tolerance: float
    multi_start_count: int
    random_seed: int
    enforce_joint_limits: bool
    singular_value_tolerance: float
    finite_difference_step: float
    max_step_rad: float
    max_step_m: float
    solution_tolerance_rad: float
    solution_tolerance_m: float
    task_mode: Literal['pose', 'position']
```

Source: `src/kincheckapi/kinematics_ik.py`.

## Import

```python
from kincheckapi.kinematics import IKOptions
```

## Purpose

Controls for numerical IK; every search and convergence limit is recorded. task_mode='position' leaves orientation unconstrained but still reports its error. Joint limits always gate acceptance. enforce_joint_limits controls projection during iteration only; disabling projection never accepts an out-of-range answer.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float` | `1e-06` | `orientation_tolerance_rad` in radians; finite. |
| `max_iterations` | `int` | `100` | Public input or data field `max_iterations`. |
| `damping` | `float` | `0.0001` | Public input or data field `damping`. |
| `step_tolerance` | `float` | `1e-09` | Public input or data field `step_tolerance`. |
| `residual_tolerance` | `float` | `1e-09` | Public input or data field `residual_tolerance`. |
| `multi_start_count` | `int` | `1` | Public input or data field `multi_start_count`. |
| `random_seed` | `int` | `0` | Public input or data field `random_seed`. |
| `enforce_joint_limits` | `bool` | `True` | Public input or data field `enforce_joint_limits`. |
| `singular_value_tolerance` | `float` | `1e-08` | Public input or data field `singular_value_tolerance`. |
| `finite_difference_step` | `float` | `1e-07` | Public input or data field `finite_difference_step`. |
| `max_step_rad` | `float` | `0.5` | `max_step_rad` in radians; finite. |
| `max_step_m` | `float` | `0.05` | `max_step_m` in metres; finite. |
| `solution_tolerance_rad` | `float` | `1e-05` | `solution_tolerance_rad` in radians; finite. |
| `solution_tolerance_m` | `float` | `1e-07` | `solution_tolerance_m` in metres; finite. |
| `task_mode` | `Literal['pose', 'position']` | `'pose'` | Public input or data field `task_mode`. |

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
