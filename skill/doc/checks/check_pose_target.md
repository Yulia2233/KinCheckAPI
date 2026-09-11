# `check_pose_target`

## API Definition

```python
check_pose_target(*, motion_result: MotionResult, targets: Optional[Sequence[Any]] = None, target: typing.Any | None = None, position_tolerance_m: float | None = None, orientation_tolerance_rad: float | None = None, start_time_s: float | None = None, end_time_s: float | None = None, check_id: str = 'pose_target') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_pose_target
```

## Purpose

Check recorded component/Connector poses against explicit targets.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `targets` | `Optional[Sequence[Any]]` | `None` | Public input or data field `targets`. |
| `target` | `Any | None` | `None` | Public input or data field `target`. |
| `position_tolerance_m` | `float | None` | `None` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float | None` | `None` | `orientation_tolerance_rad` in radians; finite. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `check_id` | `str` | `'pose_target'` | Stable caller-provided check ID for result traceability. |

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
