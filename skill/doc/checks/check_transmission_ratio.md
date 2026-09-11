# `check_transmission_ratio`

## API Definition

```python
check_transmission_ratio(*, motion_result: MotionResult, input_joint_id: str, output_joint_id: str, expected_ratio: float, expected_direction: Literal['same', 'opposite'], measurement: Literal['angular_velocity', 'linear_velocity', 'angular_displacement', 'linear_displacement', 'angular_to_linear_velocity', 'angular_to_linear_displacement'] = 'angular_velocity', start_time_s: float | None = None, end_time_s: float | None = None, relative_tolerance: float = 0.001, minimum_sample_count: int = 3, minimum_valid_fraction: float = 0.8, minimum_input_magnitude: float = 1e-09, minimum_output_magnitude: float = 1e-12, check_id: str = 'transmission_ratio') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_transmission_ratio
```

## Purpose

Compare two explicit joint curves after deterministic time alignment.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `input_joint_id` | `str` | required | Stable, resolvable `input_joint_id`. |
| `output_joint_id` | `str` | required | Stable, resolvable `output_joint_id`. |
| `expected_ratio` | `float` | required | Positive expected transmission-ratio magnitude; direction is separate. |
| `expected_direction` | `Literal['same', 'opposite']` | required | Expected output direction relative to input: `same` or `opposite`. |
| `measurement` | `Literal['angular_velocity', 'linear_velocity', 'angular_displacement', 'linear_displacement', 'angular_to_linear_velocity', 'angular_to_linear_displacement']` | `'angular_velocity'` | Public input or data field `measurement`. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `relative_tolerance` | `float` | `0.001` | Public input or data field `relative_tolerance`. |
| `minimum_sample_count` | `int` | `3` | Public input or data field `minimum_sample_count`. |
| `minimum_valid_fraction` | `float` | `0.8` | Public input or data field `minimum_valid_fraction`. |
| `minimum_input_magnitude` | `float` | `1e-09` | Public input or data field `minimum_input_magnitude`. |
| `minimum_output_magnitude` | `float` | `1e-12` | Public input or data field `minimum_output_magnitude`. |
| `check_id` | `str` | `'transmission_ratio'` | Stable caller-provided check ID for result traceability. |

## Returns and Failures

Returns `CheckReport`.

Issues, status, sample counts, and actual measurements in a structured result are part of the contract; do not check only whether the call raised an exception.

## Module Constraints

- Each check must identify its objects, time window, expected value, threshold, and units.
- A check with empty objects, empty evidence, or an incomplete MotionResult must not pass.
- Read `CheckReport.passed` together with evidence, issues, and metadata.
- Assembly integrity accepts any number of Components; `component_ids=None` checks the whole assembly.
- Mechanical, containment/guide, and geometric relations form the connection graph; record metre tolerances for geometric connections.

## Related Documentation

- [`Acceptance Checks`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
