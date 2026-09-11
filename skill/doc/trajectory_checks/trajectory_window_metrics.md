# `trajectory_window_metrics`

## API Definition

```python
trajectory_window_metrics(*, trajectory: Trajectory, start_time_s: float | None, end_time_s: float | None) -> TrajectoryWindowMetrics
```

Source: `src/kincheckapi/trajectory_checks.py`.

## Import

```python
from kincheckapi.trajectory_checks import trajectory_window_metrics
```

## Purpose

Compute sample indices, path length, and world-coordinate bounds for one component or connector trajectory over an explicit window.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `trajectory` | `Trajectory` | required | Public input or data field `trajectory`. |
| `start_time_s` | `float | None` | required | Start of the time window in seconds. |
| `end_time_s` | `float | None` | required | End of the time window in seconds. |

## Returns and Failures

Returns `TrajectoryWindowMetrics`.

## Module Constraints

- The time window must lie in the actual sample range and contain enough samples.
- Do not interpret empty windows or invalid position bounds as a pass.
- Path length and bounds are derived from discrete samples.

## Related Documentation

- [`Trajectory Utilities`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
