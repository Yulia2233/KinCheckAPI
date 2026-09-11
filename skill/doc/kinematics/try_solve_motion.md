# `try_solve_motion`

## API Definition

```python
try_solve_motion(*, scenario: Scenario, options: Any = None) -> SolveAttempt
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import try_solve_motion
```

## Purpose

Retain a structured report and `last_valid_result` after failure; never convert failure into a pass.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `options` | `Any` | `None` | Public solve or analysis options; record the effective thresholds. |

## Returns and Failures

Returns `SolveAttempt`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
