# `check_trajectory`

## API Definition

```python
check_trajectory(*, motion_result: MotionResult, component_id: str | None = None, connector_id: str | None = None, max_speed_m_s: float | None = None, max_angular_speed_rad_s: float | None = None, max_acceleration_m_s2: float | None = None, max_angular_acceleration_rad_s2: float | None = None, max_position_residual_m: float | None = None, max_orientation_residual_rad: float | None = None, min_path_length_m: float | None = None, max_path_length_m: float | None = None, position_bounds_m: Optional[Mapping[str, Sequence[float]]] = None, limit_joint_ids: Optional[Sequence[str]] = None, maximum_limit_event_count: int | None = None, maximum_exceeded_limit_event_count: int | None = 0, start_time_s: float | None = None, end_time_s: float | None = None, check_id: str = 'trajectory') -> CheckReport
```

Source: `src/kincheckapi/checks.py`.

## Import

```python
from kincheckapi.checks import check_trajectory
```

## Purpose

Check sampled trajectory ranges without modifying the result.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `motion_result` | `MotionResult` | required | The public `MotionResult` to query or check. |
| `component_id` | `str | None` | `None` | Stable, resolvable component ID. |
| `connector_id` | `str | None` | `None` | Stable, resolvable connector ID. |
| `max_speed_m_s` | `float | None` | `None` | `max_speed_m_s` in m/s; finite. |
| `max_angular_speed_rad_s` | `float | None` | `None` | `max_angular_speed_rad_s` in rad/s; finite. |
| `max_acceleration_m_s2` | `float | None` | `None` | `max_acceleration_m_s2` in m/s^2; finite. |
| `max_angular_acceleration_rad_s2` | `float | None` | `None` | Public input or data field `max_angular_acceleration_rad_s2`. |
| `max_position_residual_m` | `float | None` | `None` | `max_position_residual_m` in metres; finite. |
| `max_orientation_residual_rad` | `float | None` | `None` | `max_orientation_residual_rad` in radians; finite. |
| `min_path_length_m` | `float | None` | `None` | `min_path_length_m` in metres; finite. |
| `max_path_length_m` | `float | None` | `None` | `max_path_length_m` in metres; finite. |
| `position_bounds_m` | `Optional[Mapping[str, Sequence[float]]]` | `None` | `position_bounds_m` in metres; finite. |
| `limit_joint_ids` | `Optional[Sequence[str]]` | `None` | Explicitly specified `limit_joint_ids` collection. |
| `maximum_limit_event_count` | `int | None` | `None` | Public input or data field `maximum_limit_event_count`. |
| `maximum_exceeded_limit_event_count` | `int | None` | `0` | Public input or data field `maximum_exceeded_limit_event_count`. |
| `start_time_s` | `float | None` | `None` | Start of the time window in seconds. |
| `end_time_s` | `float | None` | `None` | End of the time window in seconds. |
| `check_id` | `str` | `'trajectory'` | Stable caller-provided check ID for result traceability. |

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
