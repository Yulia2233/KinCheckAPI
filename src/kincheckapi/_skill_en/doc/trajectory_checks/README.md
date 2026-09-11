# Trajectory Utilities

Compute trajectory-window metrics and filter joint-limit events.

## Public API

| Symbol | Type | Purpose |
| --- | --- | --- |
| [`TrajectoryWindowMetrics`](TrajectoryWindowMetrics.md) | Type | TrajectoryWindowMetrics(*, indices: 'tuple[int, ...]', path_length_m: 'float', bounds_m: 'Mapping[str, tuple[float, float]]') |
| [`limit_events_in_window`](limit_events_in_window.md) | Function | Filter recorded `LimitEvent` objects by joint ID and time window. |
| [`normalize_position_bounds`](normalize_position_bounds.md) | Function | Normalize optional position bounds into a read-only per-axis `(lower, upper)` mapping and reject invalid bounds. |
| [`trajectory_window_metrics`](trajectory_window_metrics.md) | Function | Compute sample indices, path length, and world-coordinate bounds for one component or connector trajectory over an explicit window. |

## Module Rules

- The time window must lie in the actual sample range and contain enough samples.
- Do not interpret empty windows or invalid position bounds as a pass.
- Path length and bounds are derived from discrete samples.
