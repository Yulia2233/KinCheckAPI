# `MotionEvent`

## API Definition

```python
@dataclass(frozen=True)
class MotionEvent:
    event_type: str
    time_s: float
    joint_id: str
    value: float | None
```

Source: `src/kincheckapi/motion_contracts.py`.

## Import

```python
from kincheckapi.motion_contracts import MotionEvent
```

## Purpose

Observed sample event; time_s is a recorded time, not a continuous-time proof.

## Parameters and Fields

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `event_type` | `str` | required | Public input or data field `event_type`. |
| `time_s` | `float` | required | Query time in seconds within the result time range. |
| `joint_id` | `str` | required | Stable, resolvable joint ID. |
| `value` | `float | None` | `None` | Public input or data field `value`. |

## Returns and Failures

Constructs and returns an immutable public data object; field types and ranges are validated during construction.

## Module Constraints

- Targets are immutable; time uses seconds and positions use metres.
- PoseTrajectory is an acceptance target; Cartesian driving remains a capability boundary until a 6D backend exists.
- Path and periodic contracts require explicit finite ranges and do not imply continuous-time guarantees.

## Related Documentation

- [`Motion Contract Targets`](README.md)
- [Evidence and Pass Rules](../guides/evidence-and-pass-rules.md)
