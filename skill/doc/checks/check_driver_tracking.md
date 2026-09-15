# `check_driver_tracking`

## API Definition

```python
check_driver_tracking(*, motion_result: MotionResult, scenario: 'Scenario', joint_id: str, tolerance: float = 0.001, start_time_s: float | None = None, end_time_s: float | None = None, check_id: str = 'driver_tracking') -> DriverTrackingReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_driver_tracking
```

## Purpose

Compare one declared position/speed driver to the recorded trajectory.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `scenario` | `Scenario` | required | An immutable `Scenario` bound to an assembly definition. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `tolerance` | `float` | `0.001` | Public input or data field `tolerance`. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `check_id` | `str` | `'driver_tracking'` | Stable caller-provided check ID for result traceability. |

## Returns and Failures

Returns `DriverTrackingReport`.

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
