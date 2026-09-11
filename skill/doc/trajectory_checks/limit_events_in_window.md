# `limit_events_in_window`

## API Definition

```python
limit_events_in_window(*, events: Sequence[LimitEvent], joint_ids: Optional[Sequence[str]], start_time_s: float | None, end_time_s: float | None) -> tuple[LimitEvent, ...]
```

Source: `src/kincheckapi/trajectory_checks.py`.

## Import

```python
from kincheckapi.trajectory_checks import limit_events_in_window
```

## Purpose

Filter recorded `LimitEvent` objects by joint ID and time window.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `events` | `Sequence[LimitEvent]` | required | Public input or data field `events`. |
| `joint_ids` | `Optional[Sequence[str]]` | required | Explicitly specified `joint_ids` collection. |
| `start_time_s` | `float | None` | required | Start of the time window in seconds. |
| `end_time_s` | `float | None` | required | End of the time window in seconds. |

## Returns and Failures

Returns `tuple[LimitEvent, ...]`.

## Module Constraints

- The time window must lie in the actual sample range and contain enough samples.
- Do not interpret empty windows or invalid position bounds as a pass.
- Path length and bounds are derived from discrete samples.

## Related Documentation

- [`Trajectory Utilities`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
