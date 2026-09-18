# `check_pose_trajectory`

## API Definition

```python
check_pose_trajectory(*, motion_result: MotionResult, target: Any, position_tolerance_m: float | None = None, orientation_tolerance_rad: float | None = None, check_id: str = 'pose_trajectory') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_pose_trajectory
```

## Purpose

Check a recorded component/connector trajectory against a PoseTrajectory.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `target` | `Any` | required | Public input or data field `target`. |
| `position_tolerance_m` | `float | None` | `None` | `position_tolerance_m` in metres; finite. |
| `orientation_tolerance_rad` | `float | None` | `None` | `orientation_tolerance_rad` in radians; finite. |
| `check_id` | `str` | `'pose_trajectory'` | Stable caller-provided check ID for result traceability. |

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
