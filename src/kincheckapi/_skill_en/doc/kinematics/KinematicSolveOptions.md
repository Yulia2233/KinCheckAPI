# `KinematicSolveOptions`

## API Definition

```python
@dataclass(frozen=True)
class KinematicSolveOptions:
    max_integration_step_s: float | None
    max_integration_substeps: int
    max_constraint_iterations: int
    position_residual_tolerance_m: float
    orientation_residual_tolerance_rad: float
    non_finite_state_policy: Literal['fail', 'warn']
    adaptive_sampling: bool
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import KinematicSolveOptions
```

## Purpose

Deterministic controls for backend integration and constraint solving.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `max_integration_step_s` | `float | None` | `None` | `max_integration_step_s` in seconds; finite. |
| `max_integration_substeps` | `int` | `1000000` | Public input or data field `max_integration_substeps`. |
| `max_constraint_iterations` | `int` | `100` | Public input or data field `max_constraint_iterations`. |
| `position_residual_tolerance_m` | `float` | `1e-06` | `position_residual_tolerance_m` in metres; finite. |
| `orientation_residual_tolerance_rad` | `float` | `1e-06` | `orientation_residual_tolerance_rad` in radians; finite. |
| `non_finite_state_policy` | `Literal['fail', 'warn']` | `'fail'` | Public input or data field `non_finite_state_policy`. |
| `adaptive_sampling` | `bool` | `False` | Public input or data field `adaptive_sampling`. |

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
