# `verify_transmission_ratio`

## API Definition

```python
verify_transmission_ratio(*, motion_result: MotionResult, input_joint_id: str, output_joint_id: str, expected_ratio: float, expected_direction: Literal['same', 'opposite'], measurement: str = 'angular_velocity', start_time_s: float | None = None, end_time_s: float | None = None, relative_tolerance: float = 0.001, minimum_sample_count: int = 3, minimum_valid_fraction: float = 0.8, minimum_input_magnitude: float = 1e-09, minimum_output_magnitude: float = 1e-12, check_id: str = 'transmission_ratio') -> Any
```

Source: `src/kincheckapi/kinematics.py`.

## Import

```python
from kincheckapi.kinematics import verify_transmission_ratio
```

## Purpose

Deprecated compatibility entry point; new code must use `kincheckapi.checks.check_transmission_ratio()`.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `input_joint_id` | `str` | required | Stable, resolvable `input_joint_id`. |
| `output_joint_id` | `str` | required | Stable, resolvable `output_joint_id`. |
| `expected_ratio` | `float` | required | Positive expected transmission-ratio magnitude; direction is separate. |
| `expected_direction` | `Literal['same', 'opposite']` | required | Expected output direction relative to input: `same` or `opposite`. |
| `measurement` | `str` | `'angular_velocity'` | Public input or data field `measurement`. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `relative_tolerance` | `float` | `0.001` | Public input or data field `relative_tolerance`. |
| `minimum_sample_count` | `int` | `3` | Public input or data field `minimum_sample_count`. |
| `minimum_valid_fraction` | `float` | `0.8` | Public input or data field `minimum_valid_fraction`. |
| `minimum_input_magnitude` | `float` | `1e-09` | Public input or data field `minimum_input_magnitude`. |
| `minimum_output_magnitude` | `float` | `1e-12` | Public input or data field `minimum_output_magnitude`. |
| `check_id` | `str` | `'transmission_ratio'` | Stable caller-provided check ID for result traceability. |

## Returns and Failures

Returns `Any`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Validate the assembly and Scenario before solving or analysis.
- Use `partial`, `capability_failed`, empty-sample, and unconverged results only for diagnosis, never as a pass.
- Record position, orientation, rank, and sampling thresholds explicitly; analysis does not establish dynamics or strength.
- This function emits `DeprecationWarning`; do not use it in new examples or implementations.

## Related Documentation

- [`Kinematic Solving and Analysis`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
