# `check_planar_tracking`

## API Definition

```python
check_planar_tracking(*, motion_result: MotionResult | None = None, component_id: str | None = None, connector_id: str | None = None, trajectory: Any = None, target: Any, position_tolerance_m: float = 1e-06, yaw_tolerance_rad: float = 1e-06, check_id: str = 'planar_tracking') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_planar_tracking
```

## Purpose

Check X/Y/Yaw samples. Target may be PlanarPose points or PoseTrajectory.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult | None` | `None` | The public `MotionResult` to query or check. |
| `component_id` | `str | None` | `None` | Stable, resolvable component ID. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |
| `trajectory` | `Any` | `None` | Public input or data field `trajectory`. |
| `target` | `Any` | required | Public input or data field `target`. |
| `position_tolerance_m` | `float` | `1e-06` | `position_tolerance_m` in metres; finite. |
| `yaw_tolerance_rad` | `float` | `1e-06` | `yaw_tolerance_rad` in radians; finite. |
| `check_id` | `str` | `'planar_tracking'` | Stable caller-provided check ID for result traceability. |

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
