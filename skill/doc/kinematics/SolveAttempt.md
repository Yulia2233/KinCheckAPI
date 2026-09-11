# `SolveAttempt`

## API Definition

```python
@dataclass(frozen=True)
class SolveAttempt:
    status: Literal['completed', 'completed_with_warnings', 'partial', 'validation_failed', 'capability_failed', 'failed']
    succeeded: bool
    motion_result: MotionResult | None
    last_valid_result: MotionResult | None
    report: DiagnosticReport
    failure: KinCheckError | None
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import SolveAttempt
```

## Purpose

Structured outcome returned by :func:`try_solve_motion`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `status` | `Literal['completed', 'completed_with_warnings', 'partial', 'validation_failed', 'capability_failed', 'failed']` | required | Structured status interpreted according to the stable values for the result type. |
| `succeeded` | `bool` | required | Public input or data field `succeeded`. |
| `motion_result` | `MotionResult | None` | required | The public `MotionResult` to query or check. |
| `last_valid_result` | `MotionResult | None` | required | Public input or data field `last_valid_result`. |
| `report` | `DiagnosticReport` | required | Public input or data field `report`. |
| `failure` | `KinCheckError | None` | required | Public input or data field `failure`. |

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
